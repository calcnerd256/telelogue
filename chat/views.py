from django.views.generic import (
    TemplateView,
    CreateView,
    ListView,
    DetailView,
)
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
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

    def get_queryset(self):
        qs = super(MessageListView, self).get_queryset()
        return qs.order_by("-timestamp")


class MessageDetailView(DetailView):
    model = ChatMessage


class UserDetailView(DetailView):
    model = User

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        user = self.get_object()
        context.update({
            'todo_messages': user.chatmessage_set.filter(body__icontains='TODO'),
        })
        return context
