import datetime

from django.views.generic.list import ListView

from ..models import (
    Triple,
    Listify,
)

from .base import (
    EnhancedMessageMixin,
)


class TodayView(EnhancedMessageMixin, ListView):
    page_title = "Today's Messages"
    template_name = "transit/today.html"

    @Listify
    def get_queryset(self):
        result = Triple.views.get_today()
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(1)
        tonight_midnight = datetime.datetime.fromordinal(tomorrow.toordinal())
        result = result.filter(timestamp__lte=tonight_midnight)
        for m in result.order_by("-timestamp"):
            if not m.hide:
                yield m
