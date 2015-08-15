import re
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin

# enable the admin:
admin.autodiscover()

urlpatterns = patterns(
    '',
    # url(r'^$', 'telelogue.views.home', name='home'),
    # url(r'^telelogue/', include('telelogue.foo.urls')),
    url(r'^chat/', include('chat.urls')),
    url(r'transit/', include('transit.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(
        r'^%s(?P<path>.*)$' % re.escape(settings.STATIC_URL.lstrip("/")),
        "django.contrib.staticfiles.views.serve",
        kwargs={"insecure": True},
    ),
)
