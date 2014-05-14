from nose.tools import assert_equal

from stagecraft.apps.datasets.models import(
    BackdropUser,
    DataSet,
    DataType,
    DataGroup)
from stagecraft.apps.datasets.helpers.calculate_purge_urls import (
    get_data_set_path_queries,
    get_backdrop_user_path_queries,
    _join_query_strings)


def test_get_data_set_path_queries():
    dg = DataGroup(name='dg1')
    dt = DataType(name='dt1')
    data_set = DataSet(name='ds1', data_group=dg, data_type=dt)

    expected_path_queries = set([
        '/data-sets/ds1',  # for detail view (the rest are for list view)
        '/data-sets',
        '/data-sets?data-group=dg1',
        '/data-sets?data-group=dg1&data-type=dt1',
        '/data-sets?data-group=dg1&data_type=dt1',
        '/data-sets?data-type=dt1',
        '/data-sets?data-type=dt1&data-group=dg1',
        '/data-sets?data-type=dt1&data_group=dg1',
        '/data-sets?data_group=dg1',
        '/data-sets?data_group=dg1&data-type=dt1',
        '/data-sets?data_group=dg1&data_type=dt1',
        '/data-sets?data_type=dt1',
        '/data-sets?data_type=dt1&data-group=dg1',
        '/data-sets?data_type=dt1&data_group=dg1',
    ])

    assert_equal(
        expected_path_queries,
        set(get_data_set_path_queries(data_set)))


def test_get_backdrop_user_path_queries():
    user = BackdropUser(email='wibble@email.net')

    expected_path_queries = set([
        '/users/wibble%40email.net'
    ])

    assert_equal(
        expected_path_queries,
        set(get_backdrop_user_path_queries(user)))


def test_join_query_strings():
    qs = _join_query_strings([['t=1', 'g=2'], [None, 'g=2'], [None, None]])
    assert_equal(qs, [u't=1&g=2', u'g=2', u''])
