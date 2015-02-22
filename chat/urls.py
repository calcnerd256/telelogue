from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from chat.views import (
    ChatHomeView,
    MessageCreateView,
    MessageListView,
    MessageDetailView,
    MessageExportView,
    UserDetailView,
    MessageSearchView,
)


admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^$',
        ChatHomeView.as_view(),
        name='home',
    ),

    url(
        r'^message/create/$',
        login_required(
            MessageCreateView.as_view()
        ),
        name='message_create',
    ),
    url(
        r'^message/list/$',
        login_required(
            MessageListView.as_view()
        ),
        name='message_list',
    ),
    url(
        r'^message/(?P<pk>\d+)/$',
        login_required(
            MessageDetailView.as_view()
        ),
        name='message_detail',
    ),
    url(
        r'^message/export/(?P<template>[1-90A-Za-z]+)/$',
        login_required(
            MessageExportView.as_view()
        ),
        name='message_export',
    ),

    url(
        r'^user/(?P<pk>\d+)/$',
        login_required(
            UserDetailView.as_view()
        ),
        name='user_detail',
    ),
    url(
        r'message/search/',
        login_required(
            MessageSearchView.as_view()
        ),
        name='message_search',
    ),
)
