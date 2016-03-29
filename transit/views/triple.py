from django.views.generic import (
    CreateView,
    ListView,
)
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.forms import HiddenInput

from chat.models import ChatMessage

from ..models import Triple

from .base import (
    EnhancedMessageMixin,
    super_then,
)


class CreateFromThreeMessagesView(EnhancedMessageMixin, CreateView):
    model = Triple
    page_title = 'Create triple'
    template_name = "transit/triple/create/from_messages.html"
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


class EdgeHistoryView(EnhancedMessageMixin, ListView):
    template_name = "transit/list.html"

    def get_queryset(self):
        source_pk = self.kwargs.get("source", None)
        path_pk = self.kwargs.get("path", None)
        source, path = None, None
        if source_pk and "0" != source_pk:
            source = get_object_or_404(self.model, pk=source_pk)
        if path_pk and "0" != path_pk:
            path = get_object_or_404(self.model, pk=path_pk)
        history = Triple.edges.lookup_history(source, path).order_by("-timestamp")
        return [t.destination for t in history]
