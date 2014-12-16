import json
import jsonschema
import logging
import re

from django.http import HttpResponse
from django.conf.urls import url
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

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


def resource_url(ident, cls, finder_matcher=None):
    finder_matcher = finder_matcher if finder_matcher else '<id>{}'.format(
        UUID_RE_STRING)
    return url(
        r'^{}(?:/(?P{})(?:/(?P<sub_resource>[a-z]+))?)?'.format(
            ident, finder_matcher),
        csrf_exempt(cls.as_view()))


@FORMAT_CHECKER.checks('uuid')
def is_uuid(instance):
    return isinstance(instance, str_types) and \
        UUID_RE.match(instance)


class ResourceView(View):

    model = None
    id_field = 'id'
    schema = {}
    sub_resources = {}
    list_filters = {}

    def list(self, request, additional_filters={}):
        filter_items = [
            (model_filter, request.GET.get(query_filter, None))
            for (query_filter, model_filter) in self.list_filters.items()
        ]
        filter_args = {k: v for (k, v) in filter_items if v is not None}
        #Used to filter by, for instance, backdrop user
        filter_args = dict(filter_args.items() + additional_filters.items())

        return self.model.objects.filter(**filter_args)

    def by_id(self, request, id):
        get_args = {self.id_field: id}

        try:
            return self.model.objects.get(**get_args)
        except self.model.DoesNotExist:
            return None

    def from_resource(self, request, model):
        return None

    def update_model(self, model, model_json):
        pass

    def get(self, request, **kwargs):
        id = kwargs.get(self.id_field, None)
        sub_resource = kwargs.get('sub_resource', None)

        if id is not None:
            model = self.by_id(request, id)
            if model is None:
                return HttpResponse('resource not found', status=404)
            elif sub_resource is not None:
                return self._get_sub_resource(request, sub_resource, model)
            else:
                return self._response(model)
        else:
            return self._response(self.list(request))

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

    def post(self, request, **kwargs):
        model_json, err = self._validate_json(request)
        if err:
            return err

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
            try:
                model = self.model.objects.get(id=id)
            except self.model.DoesNotExist:
                return HttpResponse(
                    'model with id {} not found'.format(id))
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
