from django.conf.urls import patterns, include, url
from django.contrib import admin

from stagecraft.apps.datasets import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    # Note that the query string params get transparently passed to the view
    url(r'^data-sets$', views.list),
    url(r'^data-sets/(?P<name>\w+)$', views.detail),
)
