from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from .views import (
    TodayView as Today,
    UnmetSemanticsView,
    CreateFromThreeMessagesView,
    UntaggedMessagesView,
    TaggedMessagesView,
    ChatMessageDetailView,
    ReplyView,
)

admin.autodiscover()

urlpatterns = patterns(
    "",
    url(
        r'^chat/today/$',
        login_required(
            Today.as_view()
        ),
        name="today",
    ),
    url(
        r'^semantic/fringe/$',
        login_required(
            UnmetSemanticsView.as_view()
        ),
        name="unmet_semantics",
    ),
    url(
        r'^triple/create_from/(?P<source>\d+)/(?P<path>\d+)/(?P<destination>\d+)/$',
        login_required(
            CreateFromThreeMessagesView.as_view()
        ),
        name="create_from_three_messages",
    ),
    url(
        r'^message/untagged/list/$',
        login_required(
            UntaggedMessagesView.as_view()
        ),
        name="untagged_messages",
    ),
    url(
        r'^message/tag/(?P<pk>\d+)/$',
        login_required(
            TaggedMessagesView.as_view()
        ),
        name="tagged_messages"
    ),
    url(
        r'^message/(?P<pk>\d+)/detail/$',
        login_required(
            ChatMessageDetailView.as_view()
        ),
        name="transit_message_detail"
    ),
    url(
        r'^message/(?P<parent>\d+)/reply/$',
        login_required(
            ReplyView.as_view()
        ),
        name="reply"
    ),
)
