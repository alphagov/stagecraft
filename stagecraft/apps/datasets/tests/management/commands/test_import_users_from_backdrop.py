from django.test import TestCase
import mock
from stagecraft.apps.datasets.models import BackdropUser

from django.core.management import call_command
from django.core.management.base import CommandError
from nose.tools import assert_raises, assert_equal


class TestImportBackdropUser(TestCase):
    fixtures = ['test_import_users_datasets.json']

    def setUp(self):
        for user in BackdropUser.objects.all():
            user.data_sets.clear()
            user.delete()

    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.purge')
    def tearDown(self, mock_purge):
        for user in BackdropUser.objects.all():
            user.data_sets.clear()
            user.delete()

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
        def _get_user(email):
            return BackdropUser.objects.filter(email=email).first()

        def _get_data_set_names(b_user):
            return set([data_set.name for data_set in b_user.data_sets.all()])

        args = ["stagecraft/apps/\
datasets/tests/fixtures/backdrop_users_import_testdata.json"]
        options = {}
        call_command('import_users_from_backdrop', *args, **options)

        backdrop_user_one = _get_user('someemail@mailtime.com')
        backdrop_user_two = _get_user('angela.merkel@deutschland.de')
        backdrop_user_three = _get_user('mike.bracken@gov.uk')

        expected_user_one_data_set_names = set(["evl_ceg_data",
                                                "evl_customer_satisfaction"])
        expected_user_two_data_set_names = set(["lpa_volumes"])

        assert_equal(
            _get_data_set_names(backdrop_user_one),
            expected_user_one_data_set_names
        )
        assert_equal(
            _get_data_set_names(backdrop_user_two),
            expected_user_two_data_set_names
        )

        assert('govuk_nonexistant_big_stats' not in
               _get_data_set_names(backdrop_user_three))

        assert_equal(set([]), _get_data_set_names(backdrop_user_three))
