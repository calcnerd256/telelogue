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

    def get_siblings(self, parent=None):
        if parent is None:
            parent = self.get_parent()
        paths = [t.path for t in parent.destination_set.all()]
        sibling_pks = [p.pk for p in filter(None, paths) if p.parent and p.parent.pk == parent.pk]
        result = self.model.objects.filter(pk__in=sibling_pks).order_by("timestamp")
        return result

    def trisect_siblings(self, message):
        parent = message.parent
        message.children = self.get_siblings(message)
        if parent is None:
            return [], message, []
        result = list(self.get_siblings(parent))
        for m in result:
            m.children = list(self.get_siblings(m))
        index = [i for i,m in enumerate(result) if m.pk == message.pk][0]
        left = result[:index]
        right = result[index+1:]
        return left, message, right

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
        parent = self.get_parent()
        context["parent"] = parent
        context["object_list"] = self.get_siblings()
        context["ancestors"] = map(self.trisect_siblings, parent.get_ancestors())
        return context
