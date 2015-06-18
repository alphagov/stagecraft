import json
import jsonschema
import logging
import re
from stagecraft.apps.users.models import User
from stagecraft.libs.authorization.http import authorize

from django.http import HttpResponse
from django.conf.urls import url
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from django.core.exceptions import ValidationError as DjangoValidationError

from django.db import DataError, IntegrityError

from jsonschema import FormatChecker
from jsonschema.compat import str_types
from jsonschema.exceptions import ValidationError
from stagecraft.libs.views.utils import create_http_error

from .transaction import atomic_view
from django.db.models import Q


logger = logging.getLogger(__name__)


UUID_RE_STRING = \
    '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
UUID_RE = re.compile(UUID_RE_STRING)
FORMAT_CHECKER = FormatChecker()


def resource_url(ident, cls):
    return url(
        resource_re_string(ident, cls),
        csrf_exempt(cls.as_view()))


def resource_re_string(ident, cls):
    id_matchers = \
        ['(?P<{}>{})'.format(k, r) for k, r in cls.id_fields.items()]
    id_matcher = '({})'.format('|'.join(id_matchers))
    return r'^{}(?:/{}(?:/(?P<sub_resource>[a-z]+))?)?'.format(
        ident, id_matcher)


@FORMAT_CHECKER.checks('uuid')
def is_uuid(instance):
    return isinstance(instance, str_types) and \
        UUID_RE.match(instance)


class ResourceView(View):

    model = None
    permissions = {
        'get': None,
        'post': None,
        'put': None,
    }
    id_fields = {
        'id': UUID_RE_STRING,
    }
    generated_id = True
    schema = {}
    sub_resources = {}
    list_filters = {}
    any_of_multiple_values_filter = {}
    order_by = 'pk'

    def list(self, request, **kwargs):
        user = kwargs.get('user', None)
        additional_filters = kwargs.get('additional_filters', {})
        unfiltered_roles = {'admin', 'dashboard-editor'}

        should_filter = user and (len(set(user['permissions']).intersection(
            unfiltered_roles)) == 0)
        can_filter = hasattr(self.model, 'owners')

        if should_filter and can_filter:
            additional_filters['owners'] = User.objects.filter(
                email=user['email'])

        query_set = self.model.objects
        query_set = self.filter_by_list_filters(
            query_set,
            request,
            additional_filters)
        query_set = self.filter_by_any_of_multiple_value_filter(
            query_set,
            request)

        return query_set.order_by(self.order_by)

    def filter_by_list_filters(self, query_set, request, additional_filters):
        filter_items = [
            (model_filter, request.GET.get(query_filter, None))
            for (query_filter, model_filter) in self.list_filters.items()
        ]
        filter_args = {k: v for (k, v) in filter_items if v is not None}
        # Used to filter by, for instance, user
        filter_args = dict(filter_args.items() + additional_filters.items())

        return query_set.filter(**filter_args).order_by('pk')

    def filter_by_any_of_multiple_value_filter(self, query_set, request):
        filter_items = None
        for (query_filter,
             model_filter) in self.any_of_multiple_values_filter.items():
            for value in request.GET.getlist(query_filter):
                if filter_items:
                    filter_items |= Q(**{model_filter: value})
                else:
                    filter_items = Q(**{model_filter: value})

        if filter_items:
            return query_set.filter(filter_items)
        else:
            return query_set

    def by_id(self, request, id_field, id, user=None):
        get_args = {id_field: id}

        try:
            model = self.model.objects.get(**get_args)
            if user and self._user_missing_model_permission(user, model):
                logger.warn("Unauthorized access to '{}' by '{}'".format(
                    id, user['email']))
                raise self.model.DoesNotExist()
            return model
        except self.model.DoesNotExist:
            return None

    def update_model(self, model, model_json, request, parent):
        pass

    def update_relationships(self, model, model_json, request, parent):
        pass

    def get(self, request, **kwargs):
        user, err = self._authorize(request)
        if err:
            return err

        id_field, id = self._find_id(kwargs)
        sub_resource = kwargs.get('sub_resource', None)

        if id is not None:
            model = self.by_id(request, id_field, id, user=user)
            if model is None:
                return create_http_error(404, 'model not found', request)
            elif sub_resource is not None:
                return self._get_sub_resource(request, sub_resource, model)
            else:
                return self._response(model)
        else:
            return self._response(self.list(request, user=user, **kwargs))

    def _find_id(self, args):
        for key, regex in self.id_fields.items():
            compiled_regex = re.compile(regex)
            if key in args and \
                    compiled_regex.match(str(args[key])) is not None:
                return key, args[key]

        return None, None

    def _user_missing_model_permission(self, user, model):
        user_is_not_admin = 'admin' not in user['permissions']
        user_is_not_assigned = hasattr(model, 'owners') and \
            model.owners.filter(email=user['email']).count() == 0

        return user_is_not_admin and user_is_not_assigned

    def _get_sub_resource(self, request, sub_resource, model):
        sub_resource = str(sub_resource.strip().lower())
        sub_view = self.sub_resources.get(sub_resource, None)

        if sub_view is not None:
            sub_view_method = getattr(sub_view, request.method.lower())
            return sub_view_method(request, **{
                'parent': model,
            })
        else:
            return create_http_error(404, 'sub resource not found', request)

    def _validate_and_save(self, model, request):
        err = self._validate_model(model, request)
        if err:
            return err

        try:
            model.save()
        except (DataError, IntegrityError) as err:
            return create_http_error(400, 'error saving model: {}'.format(err),
                                     request)

        return None

    @method_decorator(atomic_view)
    def post(self, request, **kwargs):
        user, err = self._authorize(request)
        if err:
            return err

        id_field, id = self._find_id(kwargs)
        if id is not None:
            if 'sub_resource' in kwargs:
                model = self.by_id(request, id_field, id, user=user)
                if model:
                    return self._get_sub_resource(request,
                                                  kwargs['sub_resource'],
                                                  model)
                else:
                    return create_http_error(404, 'parent resource not found',
                                             request)
            else:
                return create_http_error(405, "can't post to a resource",
                                         request)
        else:
            model_json, err = self._validate_json(request)
            if err:
                return err

            model = self.model()

            err = self.update_model(model, model_json, request,
                                    kwargs.get('parent', None))
            if err:
                return err

            err = self._validate_and_save(model, request)
            if err:
                return err

            err = self.update_relationships(
                model, model_json, request, kwargs.get('parent', None)
            )
            if err:
                return err

            err = self._validate_and_save(model, request)
            if err:
                return err

            return self._response(model)

    @method_decorator(atomic_view)
    def put(self, request, **kwargs):
        user, err = self._authorize(request)
        if err:
            return err

        id_field, id = self._find_id(kwargs)

        if id is None:
            return create_http_error(400, 'id not provided', request)

        model = self.by_id(request, id_field, id, user=user)
        if model is None:
            return create_http_error(404, 'model not found', request)

        model_json, err = self._validate_json(request)
        if err:
            return err

        err = self.update_model(model, model_json, request,
                                kwargs.get('parent', None))
        if err:
            return err

        err = self.update_relationships(
            model, model_json, request, kwargs.get('parent', None)
        )
        if err:
            return err

        err = self._validate_and_save(model, request)
        if err:
            return err

        return self._response(model)

    def _authorize(self, request):
        permission_required = self.permissions[request.method.lower()]
        return authorize(request, permission_required)

    def _validate_json(self, request):
        if request.META.get('CONTENT_TYPE', '').lower() != 'application/json':
            return None, create_http_error(415, 'bad content type', request)

        try:
            model_json = json.loads(request.body)
        except ValueError:
            return None, create_http_error(400, 'error decoding JSON: {}'
                                           .format(ValueError), request)

        try:
            jsonschema.validate(
                model_json, self.schema,
                format_checker=FORMAT_CHECKER)
        except ValidationError as err:
            message = 'options failed validation: {}'.format(err.message)
            return None, create_http_error(400, message, request)

        return model_json, None

    def _validate_model(self, model, request):
        if hasattr(model, 'validate'):
            err = model.validate()
            if err:
                return create_http_error(400, 'validation error: {}'
                                         .format(err), request)

        try:
            model.full_clean()
        except DjangoValidationError as err:
            messages = [
                '{}: {}'.format(k, ' '.join(v))
                for k, v in err.message_dict.items()
            ]
            return create_http_error(400,
                                     'validation errors:\n{}'
                                     .format('\n'.join(messages)),
                                     request)

    def _response(self, model):
        if hasattr(self.__class__, 'serialize'):
            if hasattr(model, '__iter__'):
                if hasattr(self.__class__, 'serialize_for_list'):
                    obj = [self.__class__.serialize_for_list(m) for m in model]
                else:
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
