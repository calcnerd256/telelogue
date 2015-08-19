# python imports
import datetime

# django imports
from django.db.models import Q
from django.views.generic import (
    CreateView,
    ListView,
    TemplateView,
)
from django.views.generic.detail import (
    DetailView,
    TemplateResponseMixin,
    SingleObjectMixin,
    _,
    Http404,
    models,
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
    Triple,
    FailSilently,
    SilentLookupFailure,
    Listify,
)
from chat.models import ChatMessage
from chat.views import PageTitleMixin, MessageListView

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


def super_then(clsfn, name=None):
    def decoration(fn):
        method_name = fn.__name__
        if name is not None: method_name = name
        def decorated(self, *args, **kwargs):
            method = getattr(super(clsfn(), self), method_name)
            intermediate = method(*args, **kwargs)
            result = fn(self, intermediate)
            if result is None: return intermediate
            return result
        return decorated
    return decoration


class EnhancedViewMixin(PageTitleMixin, NextOnSuccessMixin):
    @super_then(lambda: EnhancedViewMixin)
    def get_context_data(self, context):
        context["this_page"] = self.request.path
        for k in "hide sticky".split(" "):
            context["%s_pk" % k] = getattr(Triple.lookup_semantic(k), "pk", None)


class EnhancedMessageMixin(EnhancedViewMixin):
    model = ChatMessage


class CreateFromThreeMessagesView(EnhancedMessageMixin, CreateView):
    model = Triple
    page_title = 'Create triple'
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

    @super_then(lambda: CreateFromThreeMessagesView)
    def get_initial(self, result):
        result.update(self.get_messages())

    @super_then(lambda: CreateFromThreeMessagesView)
    def get_form_class(self, result):
        # TODO: make a form that knows how to do this
        for key in self.message_names:
            result.base_fields[key].widget = HiddenInput()

    @super_then(lambda: CreateFromThreeMessagesView)
    def get_context_data(self, result):
        result.update(self.get_messages())


class UnmetSemanticsView(EnhancedViewMixin, MessageListView):
    template_name = "transit/unmet_semantics.html"
    page_title = "Semantic Frontier"

    @FailSilently
    def get_candidate(self, name):
        try:
            Triple.edges.lookup_semantic(name)
            return
        except SilentLookupFailure:
            pass
        result = {"name": name}
        row = Triple.semantics[name]
        for k, name in zip("source path".split(" "), row):
            result[k] = {
                "name": name,
                "value": Triple.edges.lookup_semantic(name)
            }
        return result

    @Listify
    def get_candidates(self):
        for name in Triple.semantics.keys():
            candidate = self.get_candidate(name)
            if candidate is not None:
                yield candidate

    @super_then(lambda: UnmetSemanticsView)
    def get_context_data(self, context):
        context["semantic_fringe"] = self.get_candidates()


class UntaggedMessagesView(EnhancedViewMixin, MessageListView):
    template_name="transit/untagged_messages.html"
    page_title = "Untagged Messages"

    def get_tag(self, cascade=True):
        try:
            result = Triple.edges.lookup_semantic("tag")
            if result is not None:
                return result
            if "aggressive" == cascade:
                raise SilentFailure()
            return result
        except SilentFailure:
            if cascade:
                raise

    def get_query_filter(self, efficient=True):
        tag = self.get_tag("aggressive")
        taggings = tag.source_set.all()
        if not efficient:
            # TODO: make this fast, perhaps by inlining t.current_value()
            return ~Q(
                id__in=[
                    t.path_id
                    for t
                    in taggings
                    if t.current_value() is not None
                ]
            )
        removed = Q(
            pk__in=[
                t.path
                for t
                in taggings.filter(destination__isnull=True)
                if t.current_value() is None
            ]
        )
        never = ~Q(pk__in=taggings.values("path"))
        return removed|never

    @super_then(lambda: UntaggedMessagesView)
    @FailSilently
    def get_queryset(self, result):
        return result.filter(
            self.get_query_filter()
        ).order_by("timestamp")

    @FailSilently
    def get_tags(self):
        return list(
            Triple.util.get_tags()
        )

    @super_then(lambda: UntaggedMessagesView)
    def get_context_data(self, context):
        context.update(
            {
                "tags": self.get_tags(),
                "tag_tag": self.get_tag(False),
            }
        )


class TaggedMessagesView(EnhancedMessageMixin, TemplateView):
    template_name = "transit/tag/tagged_messages.html"
    page_title = "Tagged Messages"  # TODO: make this that helper method
    pk_url_kwarg = "pk"

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model,
            pk=int(self.kwargs.get(self.pk_url_kwarg))
        )

    def get_context_object_name(self, obj):
        if not isinstance(obj, models.Model):
            return None
        if self.object._deferred:
            obj = obj._meta.proxy_for_model
        return obj._meta.object_name.lower()

    def get_tagged_messages(self):
        tag = self.get_object()
        tag_tag = Triple.lookup_semantic("tag")
        potential_edges = tag.destination_set
        if not tag_tag: return [e.path for e in potential_edges]
        edges = potential_edges.filter(source=tag_tag)
        pks = edges.values_list("path", flat=True)
        return self.model.objects.filter(pk__in=pks)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context = {}
        if self.object:
            context["object"] = self.object
            context_object_name = self.get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(**kwargs)
        context = super(TaggedMessagesView, self).get_context_data(*args, **context)
        context["object_list"] = self.get_tagged_messages()
        return context


def fail_with(fallback):
    class result(FailSilently):
        default_value = fallback
    return result


def patch_on(target, rename=None):
    def result(fn):
        name = rename
        if name is None:
            name = fn.__name__
        setattr(target, name, fn)
        return lambda *args, **kwargs: getattr(target, name)(*args, **kwargs)
    return result


def semantic_property(fn):
    name = fn.__name__
    @property
    @FailSilently
    def decorated(self):
        return self.semantic_cache(name, fn())
    return patch_on(ChatMessage, name)(decorated)


class EnhancedMessage(ChatMessage):

    @patch_on(ChatMessage)
    def get_cache(self):
        if not hasattr(self, "_cache"):
            self._cache = {}
        return self._cache

    @patch_on(ChatMessage)
    def semantic_cache(self, lookup, semantic=None):
        if semantic is None: semantic = lookup
        cache = self.get_cache()
        if lookup in cache: return cache[lookup]
        edges = Triple.edges
        result = edges.lookup(edges.lookup_semantic(semantic), self)
        cache[lookup] = result
        return result

    @semantic_property
    def hide():
        pass

    @semantic_property
    def sticky():
        pass

    @semantic_property
    def parent():
        return "reply"

    @patch_on(ChatMessage, "tag")
    @property
    @FailSilently
    def tag(self):
        result = self.semantic_cache("tag")
        if result is None: return result
        parent = self.parent
        if parent is None: return result
        if result == FailSilently(Triple.edges.lookup_semantic("reply_tag")):
            result.get_body_preview = lambda *args, **kwargs: "a reply"
        return result

    @patch_on(ChatMessage)
    def enhance(self):
        if hasattr(self, "enhanced"): return self
        self.enhanced = True
        return self

    @patch_on(ChatMessage)
    def get_ancestors(self):
        current = self
        result = []
        while current is not None and current not in result:
            result.append(current)
            current = current.parent
        return reversed(result)


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
