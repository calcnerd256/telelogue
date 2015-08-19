# python imports
import datetime

# django imports
from django.db.models import Q
from django.views.generic import CreateView
from django.views.generic.detail import (
    DetailView,
    _,
    Http404,
    models,
)
from django.views.generic.base import (
    TemplateView,
)
from django.views.generic.list import (
    ListView,
)
from django.forms import HiddenInput
from django.shortcuts import (
    get_object_or_404,
)
from django.core.urlresolvers import (
    reverse_lazy,
)

# third-party app imports

# local app imports
from chat.models import ChatMessage
from chat.views import PageTitleMixin, MessageListView

# this app's imports
from ..models import (
    Triple,
    FailSilently,
    SilentLookupFailure,
    Listify,
    patch_on,
    semantic_property,
    cache_getter,
)

# this module's imports
from .base import (
    PageTitleMixin,
    NextOnSuccessMixin,
    super_then,
    EnhancedViewMixin,
    EnhancedMessageMixin,
    ObjectAndListView,
)

# importing views
from .triple import CreateFromThreeMessagesView
from .semantics import UnmetSemanticsView
from .tag import UntaggedMessagesView


def fail_with(fallback):
    class result(FailSilently):
        default_value = fallback
    return result


class TaggedMessagesView(EnhancedMessageMixin, ObjectAndListView):
    template_name = "transit/tag/tagged_messages.html"
    page_title = "Tagged Messages"  # TODO: make this that helper method
    pk_url_kwarg = "pk"

    def get_queryset(self):
        tag = self.get_object()
        tag_tag = Triple.lookup_semantic("tag")
        potential_edges = tag.destination_set
        if not tag_tag: return [e.path for e in potential_edges]
        edges = potential_edges.filter(source=tag_tag)
        pks = edges.values_list("path", flat=True)
        return self.model.objects.filter(pk__in=pks)


class TodayView(EnhancedMessageMixin, ListView):
    page_title = "Today's messages"
    template_name = "transit/today.html"

    @fail_with([])
    def get_sticky_messages(self):
        sticky = Triple.edges.lookup_semantic("sticky")
        stickings = sticky.source_set.all()
        stickers = (edge.path for edge in stickings if edge.current_value() is not None)
        result = self.model.objects.filter(pk__in=set(sticker.pk for sticker in stickers))
        return result.order_by("timestamp")

    def get_queryset(self):
        qs = super(TodayView, self).get_queryset()
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(1)
        yesterday_midnight = datetime.datetime.fromordinal(yesterday.toordinal()) # there must be a better way
        result = qs.filter(timestamp__gte=yesterday_midnight)
        return result.order_by("-timestamp")

    def get_context_data(self, *args, **kwargs):
        context = super(TodayView, self).get_context_data(*args, **kwargs)
        context["sticky_posts"] = self.get_sticky_messages()
        return context


class ChatMessageDetailView(EnhancedMessageMixin, DetailView):
    page_title = 'Message details (transit)'
    template_name = "transit/message_detail.html"

    def get_sources(self):
        return self.get_incidents("source", "path")

    def get_incidents(self, key, other):
        candidates = getattr(self.get_object(), "%s_set" % key).all()
        def to_pk(trip):
            message = getattr(trip, other)
            if message is None: return 0
            return message.pk

        def from_pk(pk):
            for trip in candidates:
                if pk == to_pk(trip):
                    return trip

        return [
            t.current_dict()
            for t
            in map(
                from_pk,
                set(
                    map(
                        to_pk,
                        candidates
                    )
                )
            )
        ]

    def get_paths(self):
        return self.get_incidents("path", "source")

    @Listify
    def get_destinations(self):
        ob = self.get_object()
        pk = ob.pk
        for edge in ob.destination_set.all():
            d = edge.current_value()
            if d is not None:
                if pk == d.pk:
                    yield edge

    def get_context_data(self, *args, **kwargs):
        context = super(ChatMessageDetailView, self).get_context_data(*args, **kwargs)
        context["sources"] = self.get_sources()
        context["paths"] = self.get_paths()
        context["destinations"] = self.get_destinations()
        return context


class ReplyView(EnhancedMessageMixin, CreateView):
    template_name = "transit/reply.html"

    def get_page_title(self):
        parent = self.get_parent()
        return 'Reply to "%s"' % parent.get_body_preview()

    def get_parent(self):
        pk = self.kwargs.get("parent")
        return self.model.objects.get(pk=pk)

    def get_siblings(self):
        parent = self.get_parent()
        reply = Triple.lookup_semantic("reply")
        if reply is None: return []
        destinations = [(trip, trip.current_value()) for trip in parent.destination_set.all()]
        destinations = [t for (t, d) in destinations if d is not None and d.pk == parent.pk]
        paths = [trip.path for trip in destinations if trip.source is not None and trip.source.pk == reply.pk]
        return self.model.objects.filter(pk__in=set(path.pk for path in paths if path is not None)).order_by("-timestamp")

    def form_valid(self, form):
        reply = Triple.lookup_semantic("reply")
        reply_tag = Triple.lookup_semantic("reply tag")
        tag = Triple.lookup_semantic("tag")
        if reply is None or reply_tag is None or tag is None:
            return None # TODO: fail loudly
        parent = self.get_parent()
        response = super(ReplyView, self).form_valid(form)
        result = self.object
        umbilical = Triple(source=reply, path=result, destination=parent)
        tag_edge = Triple(source=tag, path=result, destination=reply_tag)
        umbilical.save()
        tag_edge.save()
        return response

    def get_context_data(self, *args, **kwargs):
        context = super(ReplyView, self).get_context_data(*args, **kwargs)
        context["parent"] = self.get_parent()
        context["object_list"] = self.get_siblings()
        return context
