from django.conf.urls import patterns, include, url
from django.contrib import admin
from chat.views import (
    ChatHomeView,
    MessageCreateView,
    MessageListView,
    MessageDetailView,
)


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', ChatHomeView.as_view(), name='home'),
    url(r'^message/create/$', MessageCreateView.as_view(), name='message_create'),
    url(r'^message/list/$', MessageListView.as_view(), name='message_list'),
    url(r'^message/(?P<pk>\d+)/$', MessageDetailView.as_view(), name='message_detail'),
)
