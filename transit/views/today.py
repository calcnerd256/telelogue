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
        qs = super(TodayView, self).get_queryset()
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(1)
        yesterday_midnight = datetime.datetime.fromordinal(yesterday.toordinal()) # there must be a better way
        result = qs.filter(timestamp__gte=yesterday_midnight)
        for m in result.order_by("-timestamp"):
            if not m.hide:
                yield m
