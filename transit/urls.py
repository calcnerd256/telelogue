from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from .views import (
    TodayView as Today,
    DayView,
    UnmetSemanticsView,
    CreateFromThreeMessagesView,
    UntaggedMessagesView,
    TaggedMessagesView,
    ChatMessageDetailView,
    ChatMessageNeighborhoodView,
    RawMessageView,
    ReplyView,
    CorkboardView,
    CreateBagView,
    EdgeHistoryView,
)

admin.autodiscover()

urlpatterns = [
    url(
        r'^chat/',
        include(
            [
                url(
                    r'^today/$',
                    login_required(
                        Today.as_view()
                    ),
                    name="today",
                ),
                url(
                    r'^date/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$',
                    login_required(
                        DayView.as_view()
                    ),
                    name="day",
                ),
                url(
                    r'^pin/$',
                    login_required(
                        CorkboardView.as_view()
                    ),
                    name="pins"
                ),
            ]
        )
    ),
    url(
        r'^semantic/fringe/$',
        login_required(
            UnmetSemanticsView.as_view()
        ),
        name="unmet_semantics",
    ),
    url(
        r'^triple/',
        include(
            [
                url(
                    r'^create_from/(?P<source>\d+)/(?P<path>\d+)/(?P<destination>\d+)/$',
                    login_required(
                        CreateFromThreeMessagesView.as_view()
                    ),
                    name="create_from_three_messages",
                ),
                url(
                    r'^history/(?P<source>\d+)/(?P<path>\d+)/$',
                    login_required(
                        EdgeHistoryView.as_view()
                    ),
                    name="edge_history",
                )
            ]
        )
    ),
    url(
        r'^message/',
        include(
            [
                url(
                    r'^untagged/list/$',
                    login_required(
                        UntaggedMessagesView.as_view()
                    ),
                    name="untagged_messages",
                ),
                url(
                    r'^tag/(?P<pk>\d+)/$',
                    login_required(
                        TaggedMessagesView.as_view()
                    ),
                    name="tagged_messages",
                ),
                url(
                    r'^(?P<pk>\d+)/',
                    include(
                        [
                            url(
                                r'^detail/$',
                                login_required(
                                    ChatMessageDetailView.as_view()
                                ),
                                name="transit_message_detail",
                            ),
                            url(
                                r'^incident/$',
                                login_required(
                                    ChatMessageNeighborhoodView.as_view()
                                ),
                                name="message_edges",
                            ),
                            url(
                                r'^raw/$',
                                login_required(
                                    RawMessageView.as_view()
                                ),
                                name="raw_message",
                            ),
                        ]
                    )
                ),
                url(
                    r'^(?P<parent>\d+)/reply/$',
                    login_required(
                        ReplyView.as_view()
                    ),
                    name="reply",
                ),
            ]
        )
    ),
    url(
        r'^bag/create/$',
        login_required(CreateBagView.as_view()),
        name="create_bag"
    ),
]
