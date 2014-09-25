from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

import stagecraft.apps.organisation.views as organisation_views

from stagecraft.apps.datasets.views import auth as auth_views
from stagecraft.apps.datasets.views import data_set as datasets_views
from stagecraft.apps.datasets.views import backdrop_user as backdrop_user_views
from stagecraft.apps.dashboards.views import dashboard as dashboard_views
from stagecraft.apps.dashboards.views import module as module_views
from stagecraft.libs.status import views as status_views

admin.autodiscover()

uuid_regexp = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

urlpatterns = patterns(
    '',
    # Redirect / to /admin/ using a view reference
    # http://bit.ly/1qkuGZ0
    url(r'^$', RedirectView.as_view(pattern_name='admin:index')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^auth/gds/api/users/(?P<uid>[\w-]+)/reauth$', auth_views.invalidate),
    url(r'^auth/gds/api/users/(?P<uid>[\w-]+)$', auth_views.invalidate),
    # Note that the query string params get transparently passed to the view
    url(r'^data-sets$', datasets_views.list, name='data-sets-list'),
    url(r'^data-sets/$', RedirectView.as_view(pattern_name='data-sets-list',
                                              permanent=True,
                                              query_string=True)),
    url(r'^data-sets/(?P<name>[\w-]+)$', datasets_views.detail),
    # Users with access to a particular data-set
    url(r'^data-sets/(?P<dataset_name>[\w-]+)/users$', datasets_views.users,
        name='data-sets-users'
        ),
    url(r'^data-sets/(?P<dataset_name>[\w-]+)/users/$', RedirectView.as_view(
        pattern_name='data-sets-users',
        permanent=True
        )),
    url(r'^users/(?P<email>[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})$',
        backdrop_user_views.detail),
    url(r'^organisation/node$', organisation_views.root_nodes),
    url(r'^organisation/node/(?P<node_id>{})/ancestors$'.format(uuid_regexp),
        organisation_views.node_ancestors),
    url(r'^organisation/type$', organisation_views.root_types),
    url(r'^_status/data-sets$', datasets_views.health_check),
    url(r'^_status$', status_views.status),

    # Dashboards
    url(r'^dashboards$', dashboard_views.list_dashboards),
    url(r'^dashboard$', dashboard_views.dashboard, name='dashboard'),
    url(
        r'^public/dashboards$',
        dashboard_views.dashboards_for_spotlight,
        name='dashboards_for_spotlight'),
    url(r'^public/dashboards/$', RedirectView.as_view(
        pattern_name='dashboards_for_spotlight',
        permanent=True,
        query_string=True)),
    url(r'^module-type$', module_views.root_types),
    url(r'^dashboard/(?P<dashboard_id>{})/module$'.format(uuid_regexp),
        module_views.modules_on_dashboard),
    url(r'^dashboard/(?P<dashboard_id>{})$'.format(uuid_regexp),
        dashboard_views.dashboard, name='dashboard'),
)
