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
        user_messages = self.get_object().chatmessage_set.all()
        context.update(
          {
            'todo_messages': user_messages.filter(body__icontains='TODO'),
            'message_count': user_messages.count(),
            'HILY_count': user_messages.filter(body__contains='HILY').count(),
            'HGWILY_count': user_messages.filter(body__contains='HGWILY').count(),
          }
        )
        return context
