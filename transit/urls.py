from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from .views import (
    CreateFromThreeMessagesView,
)

admin.autodiscover()

urlpatterns = patterns(
    "",
    url(
        r'^triple/create_from/(?P<source>\d+)/(?P<path>\d+)/(?P<destination>\d+)/$',
        login_required(
            CreateFromThreeMessagesView.as_view()
        ),
        name="create_from_three_messages",
    ),
)
