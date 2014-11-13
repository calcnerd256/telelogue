from django.conf.urls import patterns, include, url
from django.contrib import admin
from chat.views import (
    ChatHomeView,
)


admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^$',
        ChatHomeView.as_view(),
        name='home',
    ),
)
