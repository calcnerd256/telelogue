# python imports
import datetime

# django imports
from django.db.models import Q
from django.views.generic import (
    CreateView,
    DetailView,
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
from .models import (
    lookup_semantics,
    Triple,
)
from chat.models import ChatMessage
from chat.views import MessageListView

# this app's imports


def cache_getter(name):
    def decorator(fn):
        def decorated(self, *args, **kwargs):
            if hasattr(self, name): return getattr(self, name)
            result = fn(self, *args, **kwargs)
            setattr(self, name, result)
            return result
        return decorated
    return decorator

class CreateFromThreeMessagesView(CreateView):
    model = Triple
    template_name = "transit/triple/create/from_messages.html"
    success_url = reverse_lazy("untagged_messages")

    def get_success_url(self):
        url = self.request.GET.get("next")
        if url is not None: return url
        return super(CreateFromThreeMessagesView, self).get_success_url()

    @cache_getter("source")
    def get_source(self):
        pk = self.kwargs["source"]
        if pk == "0": return None
        return get_object_or_404(ChatMessage, pk=pk)

    @cache_getter("path")
    def get_path(self):
        pk = self.kwargs["path"]
        if pk == "0": return None
        return get_object_or_404(ChatMessage, pk=pk)

    @cache_getter("destination")
    def get_destination(self):
        pk = self.kwargs["destination"]
        if pk == "0": return None
        return get_object_or_404(ChatMessage, pk=pk)

    def get_initial(self, *args, **kwargs):
        result = super(CreateFromThreeMessagesView, self).get_initial(*args, **kwargs)
        result["source"] = self.get_source()
        result["path"] = self.get_path()
        result["destination"] = self.get_destination()
        return result

    def get_form_class(self, *args, **kwargs):
        result = super(CreateFromThreeMessagesView, self).get_form_class(*args, **kwargs)
        source = result.base_fields["source"]
        path = result.base_fields["path"]
        destination = result.base_fields["destination"]
        source.widget = HiddenInput()
        path.widget = HiddenInput()
        destination.widget = HiddenInput()
        return result

    def get_context_data(self, *args, **kwargs):
        result = super(CreateFromThreeMessagesView, self).get_context_data(*args, **kwargs)
        result["source"] = self.get_source()
        result["path"] = self.get_path()
        result["destination"] = self.get_destination()
        return result


class UnmetSemanticsView(MessageListView):
    template_name = "transit/unmet_semantics.html"

    def get_candidates(self):
        def filter_step(name):
            if Triple.lookup_semantic(name) is not None: return False
            source_name, path_name = lookup_semantics[name][0:2]
            if source_name is not None:
                if Triple.lookup_semantic(source_name) is None:
                    return False
            if path_name is not None:
                if Triple.lookup_semantic(path_name) is None:
                    return False
            return True
        def map_step(name):
            source_name, path_name = lookup_semantics[name][0:2]
            source = {
                "name": source_name,
                "value": Triple.lookup_semantic(source_name),
            }
            path = {
                "name": path_name,
                "value": Triple.lookup_semantic(path_name),
            }
            return {
                "name": name,
                "source": source,
                "path": path,
            }
        return [map_step(name) for name in lookup_semantics.keys() if filter_step(name)]


    def get_context_data(self, *args, **kwargs):
        context = super(UnmetSemanticsView, self).get_context_data(*args, **kwargs)
        context["semantic_fringe"] = self.get_candidates()
        return context


class UntaggedMessagesView(MessageListView):
    template_name="transit/untagged_messages.html"
    def get_queryset(self):
        qs = super(UntaggedMessagesView, self).get_queryset()
        tag = Triple.lookup_semantic("tag")
        if tag is None: return qs
        tags = Triple.get_tags()
        taggings = Triple.objects.filter(source=tag)
        tagged = taggings.values("path")
        tag_removed = taggings.filter(destination=None).values("path")
        query = Q(pk__in=tag_removed)|~Q(pk__in=tagged)
        candidates = qs.filter(query)
        return candidates.order_by("timestamp")

    def get_context_data(self, *args, **kwargs):
        context = super(UntaggedMessagesView, self).get_context_data(*args, **kwargs)
        context["tags"] = Triple.get_tags()
        context["tag_tag"] = Triple.lookup_semantic("tag")
        return context

class TaggedMessagesView(DetailView):
    model = ChatMessage
    template_name = "transit/tag/tagged_messages.html"
    def get_tagged_messages(self):
        tag = self.get_object()
        tag_tag = Triple.lookup_semantic("tag")
        potential_edges = tag.destination_set
        if not tag_tag: return [e.path for e in potential_edges]
        edges = potential_edges.filter(source=tag_tag)
        return self.model.objects.filter(pk__in=edges.values_list("path", flat=True))

    def get_context_data(self, *args, **kwargs):
        context = super(TaggedMessagesView, self).get_context_data(*args, **kwargs)
        context["object_list"] = self.get_tagged_messages()
        return context


class TodayView(ListView):
    model = ChatMessage
    template_name = "transit/today.html"

    def get_sticky_messages(self):
        sticky = Triple.lookup_semantic("sticky")
        if sticky is None:
            return None
        stickings = sticky.source_set.all()
        stickers = (edge.path for edge in stickings if edge.current_value() is not None)
        result = self.model.objects.filter(pk__in=set(sticker.pk for sticker in stickers))
        return result.order_by("timestamp")

    def enhance_message(self, message):
        hidden = Triple.lookup_semantic("hide")
        if hidden is not None:
            message.hide = Triple.lookup(hidden, message)
        sticky = Triple.lookup_semantic("sticky")
        if sticky is not None:
            message.sticky = Triple.lookup(sticky, message)
        return message

    def get_queryset(self):
        qs = super(TodayView, self).get_queryset()
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(1)
        yesterday_midnight = datetime.datetime.fromordinal(yesterday.toordinal()) # there must be a better way
        result = qs.filter(timestamp__gte=yesterday_midnight)
        result = result.order_by("-timestamp")
        result = (self.enhance_message(message) for message in result)
        return result

    def get_context_data(self, *args, **kwargs):
        context = super(TodayView, self).get_context_data(*args, **kwargs)
        hidden = Triple.lookup_semantic("hide")
        context["hide_pk"] = hidden.pk if hidden else None
        context["this_page"] = self.request.path
        stick = Triple.lookup_semantic("sticky")
        context["sticky_pk"] = stick.pk if stick else None
        context["sticky_posts"] = (self.enhance_message(post) for post in self.get_sticky_messages())
        # force the generator so that I can reuse its results
        context["object_list"] = list(context["object_list"])
        return context

class ChatMessageDetailView(DetailView):
    model = ChatMessage
    template_name = "transit/message_detail.html"

    def get_sources(self):
        candidates = self.get_object().source_set.all()
        paths = set(
            [
                trip.path.pk if trip.path is not None else 0
                for trip
                in candidates
            ]
        )
        representatives = [
            [
                trip
                for trip
                in candidates
                if (trip.path is not None and trip.path.pk == pk)
                or (trip.path is None and pk == 0)
            ][0]
            for pk
            in paths
        ]
        return [
            {
                "source": t.source, # should be self.get_object()
                "path": t.path,
                "destination": t.current_value(),
            }
            for t
            in representatives
        ]

    def get_paths(self):
        candidates = self.get_object().path_set.all()
        sources = set(
            [
                trip.source.pk if trip.source is not None else 0
                for trip
                in candidates
            ]
        )
        representatives = [
            [
                trip
                for trip
                in candidates
                if (trip.source is not None and trip.source.pk == pk)
                or (trip.source is None and pk == 0)
            ][0]
            for pk
            in sources
        ]
        return [
            {
                "source": t.source,
                "path": t.path, # should be self.get_object()
                "destination": t.current_value(),
            }
            for t
            in representatives
        ]

    def get_destinations(self):
        ob = self.get_object()
        candidates = ob.destination_set.all()
        return [
            edge
            for edge
            in candidates
            if (
                lambda d: d is not None and d.pk == ob.pk
            )(edge.current_value())
        ]

    def get_context_data(self, *args, **kwargs):
        context = super(ChatMessageDetailView, self).get_context_data(*args, **kwargs)
        context["sources"] = self.get_sources()
        context["paths"] = self.get_paths()
        context["destinations"] = self.get_destinations()
        return context
