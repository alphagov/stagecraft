from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase
from hamcrest import (
    assert_that, has_entry, has_key, is_not, has_length, equal_to, instance_of,
    has_entries, has_items, is_not, has_property
)
from nose.tools import eq_, assert_raises

from ..models import Dashboard, Link


class DashboardTestCase(TransactionTestCase):

    def setUp(self):
        self.dashboard = Dashboard.objects.create(
            published=True,
            title="title",
            slug="slug"
        )

    def test_transaction_link(self):
        self.dashboard.update_transaction_link('blah', 'http://www.gov.uk')
        self.dashboard.update_transaction_link('blah2', 'http://www.gov.uk')
        self.dashboard.validate_and_save()
        assert_that(self.dashboard.link_set.all(), has_length(1))
        assert_that(self.dashboard.link_set.first().title, equal_to('blah2'))
        assert_that(
            self.dashboard.link_set.first().link_type,
            equal_to('transaction')
        )

    def test_other_link(self):
        self.dashboard.add_other_link('blah', 'http://www.gov.uk')
        self.dashboard.add_other_link('blah2', 'http://www.gov.uk')
        self.dashboard.validate_and_save()
        links = self.dashboard.link_set.all()

        assert_that(links, has_length(2))
        assert_that(
            links,
            has_items(
                has_property('title', 'blah'),
                has_property('title', 'blah2'),
            )
        )
        assert_that(
            self.dashboard.link_set.first().link_type,
            equal_to('other')
        )

    def test_other_and_transaction_link(self):
        self.dashboard.add_other_link('other', 'http://www.gov.uk')
        self.dashboard.add_other_link('other2', 'http://www.gov.uk')
        self.dashboard.update_transaction_link(
            'transaction',
            'http://www.gov.uk'
        )
        self.dashboard.validate_and_save()
        transaction_link = self.dashboard.get_transaction_link()
        assert_that(transaction_link, instance_of(Link))
        assert_that(
            transaction_link.link_type,
            equal_to('transaction')
        )
        assert_that(
            self.dashboard.get_other_links()[0].link_type,
            equal_to('other')
        )
        assert_that(
            self.dashboard.serialize(),
            has_entries({
                'title': 'title',
                'page-type': 'dashboard',
                'relatedPages': has_entries({
                    'improve-dashboard-message': True,
                    'transaction_link':
                    has_entries({
                        'url': 'http://www.gov.uk',
                        'title': 'transaction',
                        }),
                    'other_links':
                    has_items(
                        has_entries({
                            'url': 'http://www.gov.uk',
                            'title': 'other',
                        }),
                        has_entries({
                            'url': 'http://www.gov.uk',
                            'title': 'other2',
                        }),
                    )
                })
            })
        )

        assert_that(self.dashboard.serialize(), is_not(has_key('id')))
        assert_that(self.dashboard.serialize(), is_not(has_key('link')))
