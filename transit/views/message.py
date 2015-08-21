from django.views.generic.detail import DetailView

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
