from django.views.generic import CreateView
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

