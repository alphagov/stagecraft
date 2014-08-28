from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from uuidfield import UUIDField
from ...organisation.models import Node


def list_to_tuple_pairs(elements):
    return tuple([(element, element) for element in elements])


class Dashboard(models.Model):
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
    ]
    straplines = [
        'Dashboard',
        'Service dashboard',
        'Content dashboard',
        'Performance',
        'Policy dashboard',
        'Public sector purchasing dashboard',
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
    other_notes = models.CharField(max_length=700, blank=True)
    customer_type = models.CharField(
        max_length=20,
        choices=list_to_tuple_pairs(customer_types),
        default=customer_types[0],
        blank=True
    )
    business_model = models.CharField(
        max_length=20,
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

    def spotlightify(self):
        json = {}
        fields = [
            field for field
            in self._meta.get_all_field_names()
            if field != 'link'
            and field != 'id'
        ]
        fields = [
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
        for field in fields:
            json[field.replace('_', '-')] = getattr(self, field)

        related_pages = {}
        transaction_link = self.get_transaction_link()
        if transaction_link is not None:
            related_pages['transaction_link'] = (
                transaction_link.serialize()
            )
        related_pages['other_links'] = [
            link.serialize() for link
            in self.get_other_links()
        ]
        related_pages['improve-dashboard-message'] = (
            self.improve_dashboard_message
        )
        json['relatedPages'] = related_pages
        if self.department() is not None:
            json['department'] = self.department().spotlightify()
        if self.agency() is not None:
            json['agency'] = self.agency().spotlightify()
        print json
        return json

    def update_transaction_link(self, title, url):
        transaction_link = self.get_transaction_link()
        if transaction_link is None:
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
        if self.organisation is None:
            return None
        if self.organisation.typeOf.name == 'agency':
            return self.organisation
        return None

    def department(self):
        if self.organisation is None:
            return None
        if self.organisation.typeOf.name == 'department':
            return self.organisation
        elif self.organisation.typeOf.name == 'agency':
            if self.organisation.parent is None:
                raise ValueError
            else:
                return self.organisation.parent


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
            'url': self.url,
        }

    class Meta:
        app_label = 'dashboards'
