from django.test import TestCase
import mock
from django.core.management import call_command
from django.core.management.base import CommandError
from nose.tools import assert_raises


class TestSetToken(TestCase):
    @mock.patch("stagecraft.libs.mass_update.data_set_mass_update."
                "DataSetMassUpdate."
                "update_bearer_token_for_data_type_or_group_name")
    def test_calls_update_with_only_datatype_and_token_when_only_datatype(
            self, mock_update_bearer_token):
        token = "abc"
        args = [token]
        query = {'data_type': "789"}
        options = dict(query.items() + {'some_other_arghs': "123"}.items())
        call_command('set_token', *args, **options)
        mock_update_bearer_token.assert_called_once_with(query, token)

    @mock.patch("stagecraft.libs.mass_update.data_set_mass_update."
                "DataSetMassUpdate."
                "update_bearer_token_for_data_type_or_group_name")
    def test_calls_update_with_only_datagroup_and_token_when_only_datagroup(
            self, mock_update_bearer_token):
        token = "abc"
        args = [token]
        query = {'data_group': "789"}
        options = dict(query.items() + {'some_other_arghs': "123"}.items())
        call_command('set_token', *args, **options)
        mock_update_bearer_token.assert_called_once_with(query, token)

    @mock.patch("stagecraft.libs.mass_update.data_set_mass_update."
                "DataSetMassUpdate."
                "update_bearer_token_for_data_type_or_group_name")
    def test_calls_update_with_full_query_and_token_when_datagroup_and_type(
            self, mock_update_bearer_token):
        token = "abc"
        args = [token]
        query = {'data_group': "789", 'data_type': "blarghmargh"}
        options = dict(query.items() + {'some_other_arghs': "123"}.items())
        call_command('set_token', *args, **options)
        mock_update_bearer_token.assert_called_once_with(query, token)

    @mock.patch("stagecraft.libs.mass_update.data_set_mass_update."
                "DataSetMassUpdate."
                "update_bearer_token_for_data_type_or_group_name")
    def test_raises_command_error_when_no_token(
            self, mock_update_bearer_token):
        args = []
        query = {'data_group': "789", 'data_type': "blarghmargh"}
        options = dict(query.items() + {'some_other_arghs': "123"}.items())
        assert_raises(
            CommandError, lambda: call_command('set_token', *args, **options))

    @mock.patch("stagecraft.libs.mass_update.data_set_mass_update."
                "DataSetMassUpdate."
                "update_bearer_token_for_data_type_or_group_name")
    def test_raises_command_error_when_too_many_tokens(
            self, mock_update_bearer_token):
        args = ["some_token", "something else"]
        query = {'data_group': "789", 'data_type': "blarghmargh"}
        options = dict(query.items() + {'some_other_arghs': "123"}.items())
        assert_raises(
            CommandError, lambda: call_command('set_token', *args, **options))

    @mock.patch("stagecraft.libs.mass_update.data_set_mass_update."
                "DataSetMassUpdate."
                "update_bearer_token_for_data_type_or_group_name")
    def test_raises_command_error_when_no_datagroup_or_type(
            self, mock_update_bearer_token):
        args = ["some_token"]
        options = {'some_other_arghs': "123"}
        assert_raises(
            CommandError, lambda: call_command('set_token', *args, **options))
