from django.views.generic import CreateView

from ..models import Triple

from .base import EnhancedMessageMixin


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
