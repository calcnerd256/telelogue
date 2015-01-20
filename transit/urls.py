from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from .views import (
    UnmetSemanticsView,
)

admin.autodiscover()

urlpatterns = patterns(
    "",
    url(
        r'^semantic/fringe/$',
        login_required(
            UnmetSemanticsView.as_view()
        ),
        name="unmet_semantics",
    ),
)
