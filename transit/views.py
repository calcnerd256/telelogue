# python imports

# django imports
from django.db.models import Q
from django.views.generic import (
    CreateView,
    DetailView,
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


class ChatMessageDetailView(DetailView):
    model = ChatMessage
    template_name = "transit/message_detail.html"
