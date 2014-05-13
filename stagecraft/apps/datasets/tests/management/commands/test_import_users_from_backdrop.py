from django.test import TestCase
import mock
from stagecraft.apps.datasets.models import BackdropUser

from django.core.management import call_command
from django.core.management.base import CommandError
from nose.tools import assert_raises, assert_equal


class TestImportBackdropUser(TestCase):
    fixtures = ['test_import_users_datasets.json']

    def tearDown(self):
        BackdropUser.objects.all().delete()

    def test_raises_command_error_when_no_user_file_passed(
            self):
        args = []
        options = {}
        assert_raises(
            CommandError,
            lambda: call_command(
                'import_users_from_backdrop',
                *args, **options
            ))

    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.purge')
    def test_creates_correct_users_when_valid_file_passed_in(
            self, mock_purge):
        args = ["stagecraft/apps/\
datasets/tests/fixtures/backdrop_users_import_testdata.json"]
        options = {}
        call_command('import_users_from_backdrop', *args, **options)
        backdrop_users = BackdropUser.objects.all()
        assert_equal(len(backdrop_users), 3)
        received_emails = set(map(lambda item: item.email, backdrop_users))

        expected_emails = set(['someemail@mailtime.com',
                               'angela.merkel@deutschland.de',
                               'mike.bracken@gov.uk'])
        assert_equal(expected_emails, received_emails)

    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.purge')
    def test_creates_assigns_existing_datasets_when_valid_file_passed_in(
            self, mock_purge):
        args = ["stagecraft/apps/\
datasets/tests/fixtures/backdrop_users_import_testdata.json"]
        options = {}
        call_command('import_users_from_backdrop', *args, **options)
        backdrop_user_one = BackdropUser.objects.filter(
            email='someemail@mailtime.com').first()
        backdrop_user_two = BackdropUser.objects.filter(
            email='angela.merkel@deutschland.de').first()
        backdrop_user_three = BackdropUser.objects.filter(
            email='mike.bracken@gov.uk').first()

        expected_user_one_data_set_names = set(["lpa_volumes"])
        expected_user_two_data_set_names = set(["evl_ceg_data",
                                                "evl_customer_satisfaction"])

        assert_equal(
            set(map(
                lambda item: item.name,
                backdrop_user_one.data_sets.all())),
            expected_user_one_data_set_names)
        assert_equal(
            set(map(
                lambda item: item.name,
                backdrop_user_two.data_sets.all())),
            expected_user_two_data_set_names)
        saved_user_three_data_set_names = map(
            lambda item: item.name, backdrop_user_three.data_sets.all())
        assert_equal(
            'govuk_nonexistant_big_stats' in
            saved_user_three_data_set_names, False)
        assert_equal(saved_user_three_data_set_names, [])
