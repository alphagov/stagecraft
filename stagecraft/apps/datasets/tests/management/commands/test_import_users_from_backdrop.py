from django.test import TestCase
# import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from nose.tools import assert_raises


class TestImportBackdropUser(TestCase):

    # @mock.patch("stagecraft.libs.mass_update.data_set_mass_update."
    #             "DataSetMassUpdate."
    #             "update_bearer_token_for_data_type_or_group_name")

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

    def test_creates_correct_users_when_valid_file_passed_in(
            self):
        #import pdb
        #pdb.set_trace()
        args = ["stagecraft/apps/\
datasets/tests/fixtures/backdrop_users_import_testdata.json"]
        options = {}
        assert_raises(
            CommandError,
            lambda: call_command(
                'import_users_from_backdrop',
                *args, **options
            ))
