from chat.views import MessageListView

from ..models import Triple

from .base import EnhancedMessageMixin

class Corkboard(EnhancedMessageMixin, MessageListView):
    page_title = "Pinned Messages"
    template_name = "transit/list.html"

    def get_queryset(self):
        sticky = Triple.edges.lookup_semantic("sticky")
        stickings = sticky.source_set.all()
        pks = (edge.path_id for edge in stickings if edge.current_value() is not None)
        result = self.model.objects.filter(id__in=pks)
        return result.order_by("timestamp")
