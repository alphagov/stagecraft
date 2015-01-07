from stagecraft.libs.views.utils import(
    build_400)
import json
import jsonschema
import logging
import re
from stagecraft.apps.datasets.models import(
    BackdropUser)

from django.http import HttpResponse
from django.conf.urls import url
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from django.core.exceptions import FieldError
from django.core.exceptions import ValidationError as DjangoValidationError

from django.db import DataError, IntegrityError

from jsonschema import FormatChecker
from jsonschema.compat import str_types
from jsonschema.exceptions import ValidationError

logger = logging.getLogger(__name__)

UUID_RE_STRING = \
    '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
UUID_RE = re.compile(UUID_RE_STRING)
FORMAT_CHECKER = FormatChecker()


def resource_url(ident, cls, id_matcher=None):
    id_matcher = id_matcher if id_matcher else '<id>{}'.format(
        UUID_RE_STRING)
    return url(
        r'^{}(?:/(?P{})(?:/(?P<sub_resource>[a-z]+))?)?'.format(
            ident, id_matcher),
        csrf_exempt(cls.as_view()))


@FORMAT_CHECKER.checks('uuid')
def is_uuid(instance):
    return isinstance(instance, str_types) and \
        UUID_RE.match(instance)


class ResourceView(View):

    model = None
    id_field = 'id'
    generated_id = True
    schema = {}
    sub_resources = {}
    list_filters = {}

    def list(self, request, **kwargs):
        user = kwargs.get('user', None)
        additional_filters = kwargs.get('additional_filters', {})
        if user and 'admin' not in user['permissions']:
            additional_filters['backdropuser'] = BackdropUser.objects.filter(
                email=user['email'])

        filter_items = [
            (model_filter, request.GET.get(query_filter, None))
            for (query_filter, model_filter) in self.list_filters.items()
        ]
        filter_args = {k: v for (k, v) in filter_items if v is not None}
        # Used to filter by, for instance, backdrop user
        filter_args = dict(filter_args.items() + additional_filters.items())

        return self.model.objects.filter(**filter_args).order_by('pk')

    def by_id(self, request, id, user=None):
        get_args = {self.id_field: id}

        try:
            model = self.model.objects.get(**get_args)
            if user and self._user_missing_model_permission(user, model):
                logger.warn("Unauthorized access to '{}' by '{}'".format(
                    id, user['email']))
                raise self.model.DoesNotExist()
            return model
        except self.model.DoesNotExist:
            return None

    def from_resource(self, request, model):
        return None

    def update_model(self, model, model_json):
        pass

    def get(self, request, **kwargs):
        id = kwargs.get(self.id_field, None)
        user = kwargs.get('user', None)
        sub_resource = kwargs.get('sub_resource', None)

        if id is not None:
            model = self.by_id(request, id, user=user)
            if model is None:
                return HttpResponse('resource not found', status=404)
            elif sub_resource is not None:
                return self._get_sub_resource(request, sub_resource, model)
            else:
                return self._response(model)
        else:
            return self._response(self.list(request, user=user))

    def _user_missing_model_permission(self, user, model):
        user_is_not_admin = 'admin' not in user['permissions']
        user_is_not_assigned = model.backdropuser_set.filter(
            email=user['email']).count() == 0
        return user_is_not_admin and user_is_not_assigned

    def _get_sub_resource(self, request, sub_resource, model):
        sub_resource = str(sub_resource.strip().lower())
        sub_view = self.sub_resources.get(sub_resource, None)

        if sub_view is not None:
            resources = sub_view.from_resource(request, sub_resource, model)
            if resources is not None:
                return self._response(resources)
            else:
                return HttpResponse('sub resources not found', status=404)
        else:
            return HttpResponse('sub resource not found', status=404)

    def post(self, user, request, **kwargs):
        if 'model_json' not in kwargs:
            model_json, err = self._validate_json(request)
            if err:
                return err
        else:
            model_json = kwargs['model_json']

        model = self._get_or_create_model(model_json)

        err = self.update_model(model, model_json)
        if err:
            return err

        err = self._validate_model(model)
        if err:
            return err

        try:
            model.save()
        except (DataError, IntegrityError) as err:
            return HttpResponse('error saving model: {}'.format(err))

        return self._response(model)

    def _validate_json(self, request):
        if request.META.get('CONTENT_TYPE', '').lower() != 'application/json':
            return None, HttpResponse('bad content type', status=415)

        try:
            model_json = json.loads(request.body)
        except ValueError:
            return None, HttpResponse('bad json', status=400)

        try:
            jsonschema.validate(
                model_json, self.schema,
                format_checker=FORMAT_CHECKER)
        except ValidationError as err:
            return None, HttpResponse(
                'options failed validation: {}'.format(err.message),
                status=400)

        return model_json, None

    def _get_or_create_model(self, model_json):
        if self.id_field in model_json:
            id = model_json[self.id_field]
            if self.generated_id:
                try:
                    model = self.model.objects.get(**{self.id_field: id})
                except self.model.DoesNotExist:
                    return HttpResponse(
                        'model with id {} not found'.format(id))
            else:
                try:
                    model = self.model.objects.get(**{self.id_field: id})
                except self.model.DoesNotExist:
                    model = self.model()
        else:
            model = self.model()

        return model

    def _validate_model(self, model):
        if hasattr(model, 'validate'):
            err = model.validate()
            if err:
                return HttpResponse(err, status=400)

        try:
            model.full_clean()
        except DjangoValidationError as err:
            messages = [
                '{}: {}'.format(k, ' '.join(v))
                for k, v in err.message_dict.items()
            ]
            return HttpResponse(
                'validation errors:\n{}'.format('\n'.join(messages)),
                status=400)

    def _response(self, model):
        if hasattr(self.__class__, 'serialize'):
            if hasattr(model, '__iter__'):
                obj = [self.__class__.serialize(m) for m in model]
            else:
                obj = self.__class__.serialize(model)
        else:
            logger.info('Failed to find serialize method for model')
            obj = {}

        # throw some kind of no serializer error

        return HttpResponse(
            json.dumps(obj),
            content_type='application/json'
        )
