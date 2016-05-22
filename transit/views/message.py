import base64
import subprocess

from django.views.generic.detail import (
    DetailView,
    BaseDetailView,
)
from django.http import HttpResponse

from ..models import (
    Listify,
    Triple,
    SilentLookupFailure,
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
        pk = ob.pk if ob else 0
        seen = {}
        for edge in ob.destination_set.all():
            d = edge.current_value()
            if d is not None:
                if pk == d.pk:
                    s = edge.source
                    p = edge.path
                    spk = s.pk if s else 0
                    ppk = p.pk if p else 0
                    k = spk, ppk
                    if k not in seen:
                        yield edge
                        seen[k] = True

    def get_context_data(self, *args, **kwargs):
        context = super(ChatMessageDetailView, self).get_context_data(*args, **kwargs)
        obj = self.get_object()
        context["sources"] = list(Triple.views.get_edges_incident_on(obj))
        context["paths"] = list(
            Triple.views.get_edges_incident_on(obj, "path", "source")
        )
        context["destinations"] = list(self.get_destinations())
        return context


class ChatMessageNeighborhoodGraphView(ChatMessageNeighborhoodView):
    template_name = "transit/neighborhood.dot"

    def render_to_response(self, context, **kwargs):
        response = super(ChatMessageNeighborhoodGraphView, self).render_to_response(context, **kwargs)
        response.render()
        response["Content-Type"] = "image/svg+xml"
        kid = subprocess.Popen(["twopi", "-Tsvg"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        response.content, _ = kid.communicate(response.content)
        return response


class RawMessageView(EnhancedMessageMixin, BaseDetailView):
    response_class = HttpResponse
    content_type = "text/plain"

    def render_to_response(self, *args, **response_kwargs):
        response_kwargs.setdefault("content_type", self.content_type)
        result = self.response_class(
            content=self.body,
            **response_kwargs
        )
        return result

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.get_body()
        self.get_mimetype()
        return self.render_to_response()

    def get_mimetype(self):
        result = self.object.get_mimetype()
        if result is None: return result
        self.content_type = result
        return result

    def get_body(self):
        if not getattr(self, "object", None):
            self.object = self.get_object()
        self.body = self.object.body
        try:
            encoding = Triple.edges.lookup_semantic("base64")
            if Triple.edges.lookup(self.object, encoding):
                self.body = base64.b64decode(self.body)
        except SilentLookupFailure:
            pass
        return self.body
