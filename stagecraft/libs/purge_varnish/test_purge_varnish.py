
import mock
from nose.tools import assert_equal

from stagecraft.libs.purge_varnish import (
    purge, get_varnish_caches, get_varnish_purge_urls_for_path_queries,
    send_purge)


def test_purge():
    varnish_caches = [('https://varnish-1', 123), ('https://varnish-2', 456)]

    patch_target = ('stagecraft.libs.purge_varnish.purge_varnish.'
                    'send_purge')
    with mock.patch(patch_target) as mock_send_purge:
        purge(['/foo', '/bar'], varnish_caches=varnish_caches)

        assert_equal(
            [
                mock.call('https://varnish-1:123/foo',
                          'stagecraft.perfplat.dev'),
                mock.call('https://varnish-1:123/bar',
                          'stagecraft.perfplat.dev'),
                mock.call('https://varnish-2:456/foo',
                          'stagecraft.perfplat.dev'),
                mock.call('https://varnish-2:456/bar',
                          'stagecraft.perfplat.dev'),
            ],
            mock_send_purge.mock_calls)


def test_send_purge():

    with mock.patch('requests.request') as mock_request:
        send_purge('http://v1.fake.localdomain', 'stagecraft.perfplat.dev')
        mock_request.assert_called_once_with(
            'PURGE',
            'http://v1.fake.localdomain',
            headers={u'Host': 'stagecraft.perfplat.dev'})


def test_get_varnish_caches():
    # Note that these come from settings
    assert_equal(
	set([('http://development-1.localdomain', 7999)]),
        set(get_varnish_caches()))


def test_get_varnish_purge_urls_for_path_queries():
    patch_target = ('stagecraft.libs.purge_varnish.purge_varnish.'
                    'get_varnish_caches')
    with mock.patch(patch_target) as m:
        m.return_value = set(
            [('https://varnish-1', 1234),
             ('https://varnish-2', 4567)])

        urls = set(get_varnish_purge_urls_for_path_queries(['/url1', '/url2']))
    assert_equal(
        set([
            'https://varnish-1:1234/url1',
            'https://varnish-2:4567/url1',
            'https://varnish-1:1234/url2',
            'https://varnish-2:4567/url2',
            ]),
        urls)
