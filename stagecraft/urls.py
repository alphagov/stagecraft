from django.conf.urls import patterns, include, url
from django.contrib import admin

from stagecraft.apps.datasets import views as datasets_views
from stagecraft.libs.status import views as status_views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    # Note that the query string params get transparently passed to the view
    url(r'^data-sets$', datasets_views.list),
    url(r'^data-sets/(?P<name>[\w-]+)$', datasets_views.detail),

    url(r'^_status$', status_views.status),
)
