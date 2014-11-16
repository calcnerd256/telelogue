from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from chat.views import (
    ChatHomeView,
    MessageCreateView,
    MessageListView,
    MessageDetailView,
    UserDetailView,
)


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', ChatHomeView.as_view(), name='home'),

    url(r'^message/create/$', login_required(MessageCreateView.as_view()), name='message_create'),
    url(r'^message/list/$', login_required(MessageListView.as_view()), name='message_list'),
    url(r'^message/(?P<pk>\d+)/$', login_required(MessageDetailView.as_view()), name='message_detail'),

    url(r'^user/(?P<pk>\d+)/$', login_required(UserDetailView.as_view()), name='user_detail'),
)
