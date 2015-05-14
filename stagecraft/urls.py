from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

import stagecraft.apps.organisation.views as organisation_views
import stagecraft.apps.transforms.views as transforms_views

from stagecraft.apps.datasets.views import auth as auth_views
from stagecraft.apps.datasets.views import data_set as datasets_views
from stagecraft.apps.datasets.views import data_group as datagroups_views
import stagecraft.apps.users.views as user_views
from stagecraft.apps.dashboards.views import dashboard as dashboard_views
from stagecraft.apps.dashboards.views import module as module_views
from stagecraft.apps.dashboards.views import \
    transactions_explorer as transactions_explorer_views

from stagecraft.libs.views.resource import resource_url
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
    # Users with access to a particular data-set
    url(r'^data-sets/(?P<dataset_name>[\w-]+)/users$', datasets_views.users,
        name='data-sets-users'
        ),
    url(r'^data-sets/(?P<dataset_name>[\w-]+)/users/$', RedirectView.as_view(
        pattern_name='data-sets-users',
        permanent=True)),
    url(r'^data-sets/(?P<name>[\w-]+)/dashboard$',
        datasets_views.dashboard,
        name='data-sets-dashboard'),
    url(r'^data-sets/(?P<name>[\w-]+)/dashboard/$',
        RedirectView.as_view(
            pattern_name='data-sets-dashboard',
            permanent=True)),
    url(r'^data-sets/(?P<name>[\w-]+)/transform$',
        datasets_views.transform,
        name='data-sets-transform'),
    url(r'^data-sets/(?P<name>[\w-]+)/transform/$',
        RedirectView.as_view(
            pattern_name='data-sets-transform',
            permanent=True)),
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

    # Dashboard by UUID
    url(r'^dashboard/(?P<identifier>{})/module$'.format(uuid_regexp),
        module_views.modules_on_dashboard),
    url(r'^dashboard/(?P<identifier>{})$'.format(uuid_regexp),
        dashboard_views.dashboard, name='dashboard'),

    # Or Slug
    url(r'^dashboard/(?P<identifier>[-a-z0-9]+)/module$',
        module_views.modules_on_dashboard),
    url(r'^dashboard/(?P<identifier>[-a-z0-9]+)$',
        dashboard_views.dashboard, name='dashboard'),

    url(r'^transactions-explorer-service/(?P<identifier>[-a-z0-9]+)/dashboard',
        transactions_explorer_views.dashboards_by_tx, name='dashboards_by_tx'),

    resource_url('organisation/node', organisation_views.NodeView),
    resource_url('organisation/type', organisation_views.NodeTypeView),
    resource_url('transform-type', transforms_views.TransformTypeView),
    resource_url('transform', transforms_views.TransformView),
    resource_url('data-sets', datasets_views.DataSetView),
    resource_url('data-groups', datagroups_views.DataGroupView),
    resource_url('module', module_views.ModuleView),
    resource_url('users', user_views.UserView)
)
