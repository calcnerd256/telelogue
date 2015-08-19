from django.views.generic.detail import DetailView

from ..models import Listify

from .base import EnhancedMessageMixin


class ChatMessageDetailView(EnhancedMessageMixin, DetailView):
    page_title = "Message details (transit)"
    template_name = "transit/message_detail.html"

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
        context["sources"] = self.get_incidents("source", "path")
        context["paths"] = self.get_incidents("path", "source")
        context["destinations"] = self.get_destinations()
        return context
