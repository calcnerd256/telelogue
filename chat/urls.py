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

urlpatterns = [
    url(
        r'^$',
        ChatHomeView.as_view(),
        name='home',
    ),
    url(
        r'^message/',
        include(
            [
                url(
                    r'^create/$',
                    login_required(
                        MessageCreateView.as_view()
                    ),
                    name='message_create',
                ),
                url(
                    r'^list/$',
                    login_required(
                        MessageListView.as_view()
                    ),
                    name='message_list',
                ),
                url(
                    r'^(?P<pk>\d+)/$',
                    login_required(
                        MessageDetailView.as_view()
                    ),
                    name='message_detail',
                ),
                url(
                    r'^export/(?P<template>[1-90A-Za-z]+)/$',
                    login_required(
                        MessageExportView.as_view()
                    ),
                    name='message_export',
                ),
                url(
                    r'^search/',
                    login_required(
                        MessageSearchView.as_view()
                    ),
                    name='message_search',
                ),
            ]
        )
    ),
    url(
        r'^user/(?P<pk>\d+)/$',
        login_required(
            UserDetailView.as_view()
        ),
        name='user_detail',
    ),
]
