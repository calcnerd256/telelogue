from django.views.generic import ListView
from ..models import Triple
from .base import EnhancedMessageMixin


class TodayView(EnhancedMessageMixin, ListView):
    page_title = "Today's Messages"
    template_name = "transit/today.html"

    def get_queryset(self):
        return list(Triple.views.get_today())
