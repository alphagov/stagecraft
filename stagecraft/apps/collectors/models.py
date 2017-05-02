import json
import uuid

import jsonschema
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.query import QuerySet
from fernet_fields import EncryptedTextField
from jsonfield import JSONField

from stagecraft.apps.datasets.models import DataSet
from stagecraft.apps.users.models import User


class Provider(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=256, unique=True)

    credentials_schema = JSONField(default=dict, blank=True)

    def validate(self):
        try:
            jsonschema.Draft4Validator.check_schema(self.credentials_schema)
        except jsonschema.SchemaError as err:
            return 'schema is invalid: {}'.format(err)

        return None

    def clean(self, *args, **kwargs):
        super(Provider, self).clean(*args, **kwargs)
        validation = self.validate()

        if validation is not None:
            raise ValidationError(validation)

    def __str__(self):
        return "{}".format(self.name)


class DataSourceManager(models.Manager):
    def get_query_set(self):
        return QuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_query_set().filter(owners=user)


class DataSource(models.Model):
    objects = DataSourceManager()

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=256, unique=True)
    provider = models.ForeignKey(Provider)
    owners = models.ManyToManyField(User, blank=True)
    credentials = EncryptedTextField(default='{}')

    def validate(self):
        try:
            credentials_json = json.loads(self.credentials)
        except ValueError:
            return 'credentials are not valid JSON'

        try:
            jsonschema.validate(credentials_json,
                                self.provider.credentials_schema)
        except jsonschema.ValidationError as err:
            return 'credentials are invalid: {}'.format(err)

        return None

    def clean(self, *args, **kwargs):
        super(DataSource, self).clean(*args, **kwargs)
        validation = self.validate()

        if validation is not None:
            raise ValidationError(validation)

    def __str__(self):
        return "{}: {}".format(self.provider.name, self.name)


class CollectorType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=256, unique=True)

    provider = models.ForeignKey(Provider)

    function_validator = RegexValidator(
        '^[a-z0-9_\.]+$',
        message='Collector entry point function has to consist of lowercase'
                'letters, underscores or dots',
    )
    entry_point = models.CharField(
        max_length=200,
        unique=True,
        validators=[
            function_validator
        ]
    )
    query_schema = JSONField(default=dict, blank=True)
    options_schema = JSONField(default=dict, blank=True)

    def validate(self):
        try:
            jsonschema.Draft4Validator.check_schema(self.query_schema)
        except jsonschema.SchemaError as err:
            return 'query schema is invalid: {}'.format(err)

        try:
            jsonschema.Draft4Validator.check_schema(self.options_schema)
        except jsonschema.SchemaError as err:
            return 'options schema is invalid: {}'.format(err)

        return None

    def clean(self, *args, **kwargs):
        super(CollectorType, self).clean(*args, **kwargs)
        validation = self.validate()

        if validation is not None:
            raise ValidationError(validation)

    def __str__(self):
        return "{}: {}".format(self.provider.name, self.name)


class CollectorManager(models.Manager):
    def get_query_set(self):
        return QuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_query_set().filter(owners=user)


class Collector(models.Model):
    objects = CollectorManager()

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    slug = models.SlugField(max_length=100, unique=True)

    type = models.ForeignKey(CollectorType, related_name='collectors')
    data_source = models.ForeignKey(DataSource)
    data_set = models.ForeignKey(DataSet)

    owners = models.ManyToManyField(User, blank=True)

    query = JSONField(default=dict, blank=True)
    options = JSONField(default=dict, blank=True)

    @property
    def name(self):
        """Collector Type, Data Group Data Type."""
        return "{} {} {}".format(
            self.type.name,
            self.data_set.data_group.name,
            self.data_set.data_type.name
        )

    def validate(self, user=None):
        try:
            jsonschema.validate(self.query,
                                self.type.query_schema)
        except jsonschema.ValidationError as err:
            return 'query is invalid: {}'.format(err)

        try:
            jsonschema.validate(self.options,
                                self.type.options_schema)
        except jsonschema.ValidationError as err:
            return 'options are invalid: {}'.format(err)

        if self.type.provider.id != self.data_source.provider.id:
            msg = 'type ({}) and data source ({}) have different providers'
            return msg.format(
                self.type.provider.name,
                self.data_source.provider.name
            )

        if user is not None:
            if self.data_source.owners.filter(id=user.id).count() == 0:
                return 'the current user is not an owner of the data source'
            if self.data_set.owners.filter(id=user.id).count() == 0:
                return 'the current user is not an owner of the data set'

        return None

    def clean(self, *args, **kwargs):
        super(Collector, self).clean(*args, **kwargs)
        validation = self.validate()

        if validation is not None:
            raise ValidationError(validation)

    def __str__(self):
        return "{}".format(self.name)
