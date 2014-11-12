from django.views.generic import (
    TemplateView,
    CreateView,
    ListView,
)
from django.core.urlresolvers import reverse
from models import ChatMessage


class ChatHomeView(TemplateView):
    template_name = 'chat/home.html'


class MessageCreateView(CreateView):
    model = ChatMessage

    def get_success_url(self):
        return reverse('message_list')


class MessageListView(ListView):
    model = ChatMessage
    paginate_by = 20
