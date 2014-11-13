from django.views.generic import (
    TemplateView,
    ListView,
)
from models import ChatMessage


class ChatHomeView(TemplateView):
    template_name = 'chat/home.html'


class MessageListView(ListView):
    model = ChatMessage
    paginate_by = 20

    def get_queryset(self):
        qs = super(MessageListView, self).get_queryset()
        return qs.order_by("-timestamp")
