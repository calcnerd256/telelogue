import datetime
from django.views.generic import ListView
from ..models import Triple
from .base import EnhancedMessageMixin


class TodayView(EnhancedMessageMixin, ListView):
    page_title = "Today's Messages"
    template_name = "transit/today.html"

    def get_context_data(self, *args, **kwargs):
        context = super(TodayView, self).get_context_data(*args, **kwargs)
        today = datetime.date.today()
        yesterday = datetime.date.fromordinal(today.toordinal()-1)
        context["yesterday"] = yesterday
        return context

    def get_queryset(self):
        return list(Triple.views.get_today())


class DayView(TodayView):
    template_name = "transit/day.html"

    def get_date(self):
        today = datetime.date.today()
        year = int(self.kwargs.get("year", today.year))
        month = int(self.kwargs.get("month", today.month))
        month_day = int(self.kwargs.get("day", today.day))
        day = datetime.date(year, month, month_day)
        return day

    def get_context_data(self, *args, **kwargs):
        context = super(DayView, self).get_context_data(*args, **kwargs)
        today = self.get_date().toordinal()
        tomorrow = datetime.date.fromordinal(today + 1)
        yesterday = datetime.date.fromordinal(today - 1)
        context["tomorrow"] = tomorrow
        context["yesterday"] = yesterday
        context["today"] = self.get_date()
        return context

    def get_queryset(self):
        day = self.get_date()
        return list(Triple.views.get_day(day))
