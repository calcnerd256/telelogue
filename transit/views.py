# python imports

# django imports
from django.views.generic import (
    CreateView,
)
from django.forms import HiddenInput
from django.shortcuts import (
    get_object_or_404,
)

# third-party app imports

# local app imports
from .models import (
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
