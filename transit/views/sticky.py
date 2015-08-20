from chat.views import MessageListView
from ..models import Triple
from .base import EnhancedMessageMixin

class Corkboard(EnhancedMessageMixin, MessageListView):
    page_title = "Pinned Messages"
    template_name = "transit/list.html"

    def get_queryset(self):
        return Triple.views.get_sticky_posts()
