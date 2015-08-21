from django.views.generic.detail import (
    DetailView,
    BaseDetailView,
)
from django.http import HttpResponse

from ..models import (
    Listify,
    Triple,
)

from .base import EnhancedMessageMixin


class ChatMessageDetailView(EnhancedMessageMixin, DetailView):
    page_title = "Message details (transit)"
    template_name = "transit/message_detail.html"

class ChatMessageNeighborhoodView(ChatMessageDetailView):
    page_title = "Incident edges"
    template_name = "transit/neighborhood.html"

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
        obj = self.get_object()
        context["sources"] = list(Triple.views.get_edges_incident_on(obj))
        context["paths"] = list(
            Triple.views.get_edges_incident_on(obj, "path", "source")
        )
        context["destinations"] = list(self.get_destinations())
        return context


class RawMessageView(EnhancedMessageMixin, BaseDetailView):
    response_class = HttpResponse
    content_type = None

    def render_to_response(self, *args, **response_kwargs):
        response_kwargs.setdefault("content_type", self.content_type)
        result = self.response_class(
            content=self.body,
            **response_kwargs
        )
        return result

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.body = self.object.body
        content_type = self.get_mimetype()
        if content_type is not None:
            self.content_type = content_type
        return self.render_to_response()

    def get_mimetype(self):
        return self.object.get_mimetype()
