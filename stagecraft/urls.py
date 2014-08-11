from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

from stagecraft.apps.datasets.views import auth as auth_views
from stagecraft.apps.datasets.views import data_set as datasets_views
from stagecraft.apps.datasets.views import backdrop_user as backdrop_user_views
from stagecraft.libs.status import views as status_views

admin.autodiscover()

urlpatterns = patterns(
    '',
    # Redirect / to /admin/ using a view reference
    # http://bit.ly/1qkuGZ0
    url(r'^$', RedirectView.as_view(pattern_name='admin:index')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^auth/gds/api/users/(?P<uid>[\w-]+)/reauth', auth_views.reauth),
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
    url(r'^_status/data-sets$', datasets_views.health_check),
    url(r'^_status$', status_views.status),
)
