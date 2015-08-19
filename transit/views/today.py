import datetime

from django.views.generic.list import ListView

from ..models import Triple

from .base import (
    EnhancedMessageMixin,
    fail_with,
)


class TodayView(EnhancedMessageMixin, ListView):
    page_title = "Today's Messages"
    template_name = "transit/today.html"

    @fail_with([])
    def get_sticky_messages(self):
        sticky = Triple.edges.lookup_semantic("sticky")
        stickings = sticky.source_set.all()
        stickers = (edge.path for edge in stickings if edge.current_value() is not None)
        result = self.model.objects.filter(pk__in=(sticker.pk for sticker in stickers))
        return result.order_by("timestamp")

    def get_queryset(self):
        qs = super(TodayView, self).get_queryset()
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(1)
        yesterday_midnight = datetime.datetime.fromordinal(yesterday.toordinal()) # there must be a better way
        result = qs.filter(timestamp__gte=yesterday_midnight)
        return result.order_by("-timestamp")

    def get_context_data(self, *args, **kwargs):
        context = super(TodayView, self).get_context_data(*args, **kwargs)
        context["sticky_posts"] = self.get_sticky_messages()
        return context
