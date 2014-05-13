from __future__ import unicode_literals

from itertools import chain, product

from django.core import urlresolvers


def get_backdrop_user_path_queries(user):
    """
    Return all the possible URL paths for a given user, eg:

    - /users/user%40email.com
    ...etc
    """
    # we import here to avoid a circular import
    from stagecraft.apps.datasets.views.backdrop_user import \
        detail as backdrop_user_detail_view
    return (_get_url_path_queries_for_detail_view(
            user, 'email', backdrop_user_detail_view))


def get_data_set_path_queries(data_set):
    """
    Return all the possible URL paths for a given data set, eg:

    - /data-sets/govuk_visitors
    - /data-sets/data_group=govuk&data-type=visitors"
    ...etc
    """
    # we import here to avoid a circular import
    from stagecraft.apps.datasets.views.data_set import \
        detail as data_set_detail_view
    return (_get_url_path_queries_for_list_view(data_set)
            | _get_url_path_queries_for_detail_view(
                data_set, 'name', data_set_detail_view))


def _get_url_path_queries_for_list_view(data_set):
    data_group_key_vals = [
        None,
        'data-group={}'.format(data_set.data_group.name),
        'data_group={}'.format(data_set.data_group.name),
    ]
    data_type_key_vals = [
        None,
        'data-type={}'.format(data_set.data_type.name),
        'data_type={}'.format(data_set.data_type.name),
    ]

    parameter_pairs = chain(  # permutations
        product(data_group_key_vals, data_type_key_vals),
        product(data_type_key_vals, data_group_key_vals))

    query_strings = set(_join_query_strings(parameter_pairs))

    # we import here to avoid a circular import
    from stagecraft.apps.datasets.views.data_set import \
        list as data_set_list_view
    path = urlresolvers.reverse(data_set_list_view)
    path_queries = ['{}?{}'.format(path, qs)
                    if qs else path for qs in query_strings]

    return set(path_queries)


def _get_url_path_queries_for_detail_view(item, identifier, view):
    path = urlresolvers.reverse(
        view, kwargs={identifier: getattr(item, identifier)})
    return set([path])


def _join_query_strings(parameter_pairs):
    """
    This creates a list of query strings from pairs of parameters.
    """
    filtered = [filter(None, pair) for pair in parameter_pairs]
    return ['&'.join(pair) for pair in filtered]
