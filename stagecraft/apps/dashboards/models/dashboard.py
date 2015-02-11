from django.core.validators import RegexValidator
from django.db import models
from uuidfield import UUIDField

from stagecraft.apps.organisation.views import NodeView


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
              AND dashboards_dashboard.published=TRUE
        ''', [filter_string])


class Dashboard(models.Model):
    objects = DashboardManager()

    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
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
    published = models.BooleanField()
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=500, blank=True)
    description_extra = models.CharField(max_length=400, blank=True)
    costs = models.CharField(max_length=1500, blank=True)
    other_notes = models.CharField(max_length=1000, blank=True)
    customer_type = models.CharField(
        max_length=20,
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
    organisation = models.ForeignKey(
        'organisation.Node', blank=True, null=True)

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
        dashboards = Dashboard.objects.filter(published=True)

        def spotlightify_for_list(item):
            return item.spotlightify_for_list()
        return {
            'page-type': 'browse',
            'items': map(spotlightify_for_list, dashboards),
        }

    def spotlightify_for_list(self):
        base_dict = self.list_base_dict()
        if self.department():
            base_dict['department'] = self.department().spotlightify()
        if self.agency():
            base_dict['agency'] = self.agency().spotlightify()
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
        base_dict['modules'] = [
            m.spotlightify()
            for m in self.module_set.filter(parent=None).order_by('order')]
        base_dict['relatedPages'] = self.related_pages_dict()
        if self.department():
            base_dict['department'] = self.department().spotlightify()
        if self.agency():
            base_dict['agency'] = self.agency().spotlightify()
        return get_modules_or_tabs(request_slug, base_dict)

    def serialize(self):
        serialized = {}
        fields = self._meta.get_fields_with_model()
        field_names = [field.name for field, _ in fields]

        for field in field_names:
            value = getattr(self, field)
            serialized[field] = value

        if self.organisation:
            serialized['organisation'] = NodeView.serialize(self.organisation)

        serialized['links'] = [link.serialize()
                               for link in self.link_set.all()]

        serialized['modules'] = self.serialized_modules()

        return serialized

    def serialized_modules(self):
        return [m.serialize()
                for m in self.module_set.filter(parent=None).order_by('order')]

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

    def agency(self):
        if not self.organisation:
            return None
        if self.organisation.typeOf.name == 'agency':
            return self.organisation
        return None

    def department(self):
        agency = self.agency()
        if agency:
            parent = agency.parents.first()
            if not parent:
                raise ValueError
            else:
                return parent
        else:
            return self.organisation


class Link(models.Model):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
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
