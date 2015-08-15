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
    FailSilently,
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


class NextOnSuccessMixin(object):
    def get_success_url(self):
        url = self.request.GET.get("next")
        if url is not None: return url
        return super(NextOnSuccessMixin, self).get_success_url()


class CreateFromThreeMessagesView(NextOnSuccessMixin, CreateView):
    model = Triple
    template_name = "transit/triple/create/from_messages.html"
    success_url = reverse_lazy("untagged_messages")
    message_names = "source path destination".split(" ")

    def get_message(self, name):
        if hasattr(self, name): return getattr(self, name)
        pk = int(self.kwargs[name])  # fail loudly
        if 0 == pk: return None  # don't even cache it
        result = get_object_or_404(ChatMessage, pk=pk)
        setattr(self, name, result)
        return result

    def get_messages(self):
        names = self.message_names
        return dict(zip(names, map(self.get_message, names)))

    def get_initial(self, *args, **kwargs):
        result = super(CreateFromThreeMessagesView, self).get_initial(*args, **kwargs)
        result.update(self.get_messages())
        return result

    def get_form_class(self, *args, **kwargs):
        result = super(CreateFromThreeMessagesView, self).get_form_class(*args, **kwargs)
        for key in self.message_names:
            result.base_fields[key].widget = HiddenInput()
        return result

    def get_context_data(self, *args, **kwargs):
        result = super(CreateFromThreeMessagesView, self).get_context_data(*args, **kwargs)
        result.update(self.get_messages())
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
        names = lookup_semantics.keys()
        return map(map_step, filter(filter_step, names))


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

    @classmethod
    def annotate_objects(cls, object_list):
        tag = Triple.lookup_semantic("tag")
        if tag is None: return
        for message in object_list:
            message.tag = Triple.lookup(tag, message)

    def get_context_data(self, *args, **kwargs):
        context = super(UntaggedMessagesView, self).get_context_data(*args, **kwargs)
        context["tags"] = Triple.get_tags()
        context["tag_tag"] = Triple.lookup_semantic("tag")
        self.annotate_objects(context["object_list"])
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


def fail_with(fallback):
    class result(FailSilently):
        default_value = fallback
    return result


class TodayView(ListView):
    model = ChatMessage
    template_name = "transit/today.html"

    @fail_with([])
    def get_sticky_messages(self):
        sticky = Triple.edges.lookup_semantic("sticky")
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

        reply = Triple.lookup_semantic("reply")
        if reply is not None:
            message.parent = Triple.lookup(reply, message)

        tag = Triple.lookup_semantic("tag")
        if tag is not None:
            message.tag = Triple.lookup(tag, message)
            reply_tag = Triple.lookup_semantic("reply tag")
            if reply_tag is not None and message.tag is not None:
                if reply_tag.pk == message.tag.pk:
                    if message.parent:
                        message.tag = {
                            "pk": message.tag.pk,
                            "get_body_preview": "a reply",
                        }

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
        context["sticky_posts"] = map(self.enhance_message, self.get_sticky_messages())
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


class ReplyView(NextOnSuccessMixin, CreateView):
    model = ChatMessage
    template_name = "transit/reply.html"

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
