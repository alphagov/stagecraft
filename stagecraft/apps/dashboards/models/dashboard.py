from __future__ import unicode_literals
import uuid
from django.core.validators import RegexValidator
from django.db import models

from stagecraft.apps.users.models import User
from stagecraft.apps.organisation.views import NodeView
from django.db.models.query import QuerySet


def list_to_tuple_pairs(elements):
    return tuple([(element, element) for element in elements])


class DashboardManager(models.Manager):

    def by_tx_id(self, tx_id):
        filter_string = '"service_id:{}"'.format(tx_id)
        return self.raw('''
            SELECT DISTINCT dashboards_dashboard.*
            FROM dashboards_module
              INNER JOIN dashboards_dashboard ON
                dashboards_dashboard.id = dashboards_module.dashboard_id,
              json_array_elements(query_parameters->'filter_by') AS filters
            WHERE filters::text = %s
              AND data_set_id=(SELECT id FROM datasets_dataset
                               WHERE name='transactional_services_summaries')
              AND dashboards_dashboard.status='published'
        ''', [filter_string])

    def get_query_set(self):
        return QuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_query_set().filter(owners=user)


class Dashboard(models.Model):
    objects = DashboardManager()

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    slug_validator = RegexValidator(
        '^[-a-z0-9]+$',
        message='Slug can only contain lower case letters, numbers or hyphens'
    )
    slug = models.CharField(
        max_length=90,
        unique=True,
        validators=[
            slug_validator
        ]
    )
    owners = models.ManyToManyField(User)

    dashboard_types = [
        'transaction',
        'high-volume-transaction',
        'service-group',
        'agency',
        'department',
        'content',
        'other',
    ]
    customer_types = [
        '',
        'Business',
        'Individuals',
        'Business and individuals',
        'Charity',
    ]
    business_models = [
        '',
        'Department budget',
        'Fees and charges',
        'Taxpayers',
        'Fees and charges, and taxpayers',
    ]
    straplines = [
        'Dashboard',
        'Service dashboard',
        'Content dashboard',
        'Performance',
        'Policy dashboard',
        'Public sector purchasing dashboard',
        'Topic Explorer',
        'Service Explorer',
    ]

    dashboard_type = models.CharField(
        max_length=30,
        choices=list_to_tuple_pairs(dashboard_types),
        default=dashboard_types[0]
    )
    page_type = models.CharField(max_length=80, default='dashboard')
    status = models.CharField(
        max_length=30,
        default='unpublished'
    )
    title = models.CharField(max_length=256)
    description = models.CharField(max_length=500, blank=True)
    description_extra = models.CharField(max_length=400, blank=True)
    costs = models.CharField(max_length=1500, blank=True)
    other_notes = models.CharField(max_length=1000, blank=True)
    customer_type = models.CharField(
        max_length=30,
        choices=list_to_tuple_pairs(customer_types),
        default=customer_types[0],
        blank=True
    )
    business_model = models.CharField(
        max_length=31,
        choices=list_to_tuple_pairs(business_models),
        default=business_models[0],
        blank=True
    )
    # 'department' is not being considered for now
    # 'agency' is not being considered for now
    improve_dashboard_message = models.BooleanField(default=True)
    strapline = models.CharField(
        max_length=40,
        choices=list_to_tuple_pairs(straplines),
        default=straplines[0]
    )
    tagline = models.CharField(max_length=400, blank=True)
    _organisation = models.ForeignKey(
        'organisation.Node', blank=True, null=True,
        db_column='organisation_id')

    @property
    def published(self):
        return self.status == 'published'

    @published.setter
    def published(self, value):
        if value is True:
            self.status = 'published'
        else:
            self.status = 'unpublished'

    @property
    def organisation(self):
        return self._organisation

    @organisation.setter
    def organisation(self, node):
        self.department_cache = None
        self.agency_cache = None
        self.service_cache = None
        self.transaction_cache = None

        self._organisation = node
        if node is not None:
            for n in node.get_ancestors(include_self=True):
                if n.typeOf.name == 'department':
                    self.department_cache = n
                elif n.typeOf.name == 'agency':
                    self.agency_cache = n
                elif n.typeOf.name == 'service':
                    self.service_cache = n
                elif n.typeOf.name == 'transaction':
                    self.transaction_cache = n

    # Denormalise org tree for querying ease.
    department_cache = models.ForeignKey(
        'organisation.Node', blank=True, null=True,
        related_name='dashboards_owned_by_department')
    agency_cache = models.ForeignKey(
        'organisation.Node', blank=True, null=True,
        related_name='dashboards_owned_by_agency')
    service_cache = models.ForeignKey(
        'organisation.Node', blank=True, null=True,
        related_name='dashboards_owned_by_service')
    transaction_cache = models.ForeignKey(
        'organisation.Node', blank=True, null=True,
        related_name='dashboards_owned_by_transaction')

    spotlightify_base_fields = [
        'business_model',
        'costs',
        'customer_type',
        'dashboard_type',
        'description',
        'description_extra',
        'other_notes',
        'page_type',
        'published',
        'slug',
        'strapline',
        'tagline',
        'title'
    ]

    list_base_fields = [
        'slug',
        'title',
        'dashboard_type'
    ]

    @classmethod
    def list_for_spotlight(cls):
        dashboards = Dashboard.objects.filter(status='published')\
            .select_related('department_cache', 'agency_cache',
                            'service_cache')

        def spotlightify_for_list(item):
            return item.spotlightify_for_list()
        return {
            'page-type': 'browse',
            'items': map(spotlightify_for_list, dashboards),
        }

    def spotlightify_for_list(self):
        base_dict = self.list_base_dict()
        if self.department_cache is not None:
            base_dict['department'] = self.department_cache.spotlightify()
        if self.agency_cache is not None:
            base_dict['agency'] = self.agency_cache.spotlightify()
        if self.service_cache is not None:
            base_dict['service'] = self.service_cache.spotlightify()
        return base_dict

    def spotlightify_base_dict(self):
        base_dict = {}
        for field in self.spotlightify_base_fields:
            base_dict[field.replace('_', '-')] = getattr(self, field)
        return base_dict

    def list_base_dict(self):
        base_dict = {}
        for field in self.list_base_fields:
            base_dict[field.replace('_', '-')] = getattr(self, field)
        return base_dict

    def related_pages_dict(self):
        related_pages_dict = {}
        transaction_link = self.get_transaction_link()
        if transaction_link:
            related_pages_dict['transaction'] = (
                transaction_link.serialize())

        related_pages_dict['other'] = [
            link.serialize() for link
            in self.get_other_links()
        ]
        related_pages_dict['improve-dashboard-message'] = (
            self.improve_dashboard_message
        )
        return related_pages_dict

    def spotlightify(self, request_slug=None):
        base_dict = self.spotlightify_base_dict()
        base_dict['modules'] = self.spotlightify_modules()
        base_dict['relatedPages'] = self.related_pages_dict()
        if self.department():
            base_dict['department'] = self.spotlightify_department()
        if self.agency():
            base_dict['agency'] = self.spotlightify_agency()
        modules_or_tabs = get_modules_or_tabs(request_slug, base_dict)
        return modules_or_tabs

    def serialize(self):
        def simple_field(field):
            return not (field.is_relation or field.one_to_one or (
                field.many_to_one and field.related_model))

        serialized = {}
        fields = self._meta.get_fields()
        field_names = [field.name for field in fields
                       if simple_field(field)]

        for field in field_names:
            if not (field.startswith('_') or field.endswith('_cache')):
                value = getattr(self, field)
                serialized[field] = value

        if self.status == 'published':
            serialized['published'] = True
        else:
            serialized['published'] = False

        if self.organisation:
            serialized['organisation'] = NodeView.serialize(self.organisation)
        else:
            serialized['organisation'] = None

        serialized['links'] = [link.serialize()
                               for link in self.link_set.all()]

        serialized['modules'] = self.serialized_modules()

        return serialized

    def serialized_modules(self):
        return [m.serialize()
                for m in self.module_set.filter(parent=None).order_by('order')]

    def spotlightify_modules(self):
        return [m.spotlightify() for m in
                self.module_set.filter(parent=None).order_by('order')]

    def spotlightify_agency(self):
        return self.agency().spotlightify()

    def spotlightify_department(self):
        return self.department().spotlightify()

    def update_transaction_link(self, title, url):
        transaction_link = self.get_transaction_link()
        if not transaction_link:
            self.link_set.create(
                title=title,
                url=url,
                link_type='transaction'
            )
        else:
            link = transaction_link
            link.title = title
            link.url = url
            link.save()

    def add_other_link(self, title, url):
        self.link_set.create(
            title=title,
            url=url,
            link_type='other'
        )

    def get_transaction_link(self):
        transaction_link = self.link_set.filter(link_type='transaction')
        if len(transaction_link) == 1:
            return transaction_link[0]
        else:
            return None

    def get_other_links(self):
        return self.link_set.filter(link_type='other').all()

    def validate_and_save(self):
        self.full_clean()
        self.save()

    class Meta:
        app_label = 'dashboards'

    def organisations(self):
        department = None
        agency = None
        if self.organisation is not None:
            for node in self.organisation.get_ancestors(include_self=False):
                if node.typeOf.name == 'department':
                    department = node
                if node.typeOf.name == 'agency':
                    agency = node
        return department, agency

    def agency(self):
        if self.organisation is not None:
            if self.organisation.typeOf.name == 'agency':
                return self.organisation
            for node in self.organisation.get_ancestors():
                if node.typeOf.name == 'agency':
                    return node
        return None

    def department(self):
        if self.agency() is not None:
            dept = None
            for node in self.agency().get_ancestors(include_self=False):
                if node.typeOf.name == 'department':
                    dept = node
            return dept
        else:
            if self.organisation is not None:
                for node in self.organisation.get_ancestors():
                    if node.typeOf.name == 'department':
                        return node
        return None


class Link(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    title = models.CharField(max_length=100)
    url = models.URLField(max_length=200)
    dashboard = models.ForeignKey(Dashboard)
    link_types = [
        'transaction',
        'other',
    ]
    link_type = models.CharField(
        max_length=20,
        choices=list_to_tuple_pairs(link_types),
    )

    def serialize(self):
        return {
            'title': self.title,
            'type': self.link_type,
            'url': self.url
        }

    class Meta:
        app_label = 'dashboards'


def get_modules_or_tabs(request_slug, dashboard_json):
    # first part will always be empty as we never end the dashboard slug with
    # a slash
    if request_slug is None:
        return dashboard_json
    module_slugs = request_slug.replace(
        dashboard_json['slug'], '').split('/')[1:]
    if len(module_slugs) == 0:
        return dashboard_json
    if 'modules' not in dashboard_json:
        return None
    modules = dashboard_json['modules']
    for slug in module_slugs:
        module = find_first_item_matching_slug(modules, slug)
        if module is None:
            return None
        elif module['modules']:
            modules = module['modules']
            dashboard_json['modules'] = [module]
        elif 'tabs' in module:
            last_slug = module_slugs[-1]
            if last_slug == slug:
                dashboard_json['modules'] = [module]
            else:
                tab_slug = last_slug.replace(slug + '-', '')
                tab = get_single_tab_from_module(tab_slug, module)
                if tab is None:
                    return None
                else:
                    tab['info'] = module['info']
                    tab['title'] = module['title'] + ' - ' + tab['title']
                    dashboard_json['modules'] = [tab]
            break
        else:
            dashboard_json['modules'] = [module]
    dashboard_json['page-type'] = 'module'
    return dashboard_json


def get_single_tab_from_module(tab_slug, module_json):
    return find_first_item_matching_slug(module_json['tabs'], tab_slug)


def find_first_item_matching_slug(item_list, slug):
    for item in item_list:
        if item['slug'] == slug:
            return item
