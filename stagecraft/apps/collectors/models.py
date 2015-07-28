import json
import jsonschema
import uuid
from django.core.validators import RegexValidator
from django.db import models
from django_field_cryptography import fields as encrypted_fields
from jsonfield import JSONField
from stagecraft.apps.datasets.models import DataSet
from stagecraft.apps.users.models import User
from jsonschema import ValidationError, Draft3Validator, SchemaError


class Provider(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=256, unique=True)

    credentials_schema = JSONField(default={}, blank=True)

    def validate(self):
        try:
            Draft3Validator.check_schema(self.credentials_schema)
        except SchemaError as err:
            return 'schema is invalid: {}'.format(err)

        return None


class DataSource(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=256, unique=True)

    provider = models.ForeignKey(Provider)

    owners = models.ManyToManyField(User, blank=True)

    credentials = encrypted_fields.EncryptedTextField(default='{}')

    def validate(self):
        try:
            credentials_json = json.loads(self.credentials)
        except ValueError:
            return 'credentials are not valid JSON'

        try:
            jsonschema.validate(credentials_json,
                                self.provider.credentials_schema)
        except ValidationError as err:
            return 'credentials are invalid: {}'.format(err)

        return None


class CollectorType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=256, unique=True)

    slug_validator = RegexValidator(
        '^[-a-z0-9]+$',
        message='Slug can only contain lower case letters, numbers or hyphens'
    )
    slug = models.CharField(
        max_length=256,
        unique=True,
        validators=[
            slug_validator
        ]
    )

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
    query_schema = JSONField(default={}, blank=True)
    options_schema = JSONField(default={}, blank=True)

    def validate(self):
        try:
            Draft3Validator.check_schema(self.query_schema)
        except SchemaError as err:
            return 'query schema is invalid: {}'.format(err)

        try:
            Draft3Validator.check_schema(self.options_schema)
        except SchemaError as err:
            return 'options schema is invalid: {}'.format(err)

        return None


class Collector(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    type = models.ForeignKey(CollectorType)
    data_source = models.ForeignKey(DataSource)
    data_set = models.ForeignKey(DataSet)

    owners = models.ManyToManyField(User, blank=True)

    query = JSONField(default={}, blank=True)
    options = JSONField(default={}, blank=True)

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
        except ValidationError as err:
            return 'query is invalid: {}'.format(err)

        try:
            jsonschema.validate(self.options,
                                self.type.options_schema)
        except ValidationError as err:
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
