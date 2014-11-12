from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from chat.views import (
    ChatHomeView,
    MessageCreateView,
    MessageListView,
)


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', ChatHomeView.as_view(), name='home'),
    url(r'^message/create/$', login_required(MessageCreateView.as_view()), name='message_create'),
    url(r'^message/list/$', login_required(MessageListView.as_view()), name='message_list'),
)
