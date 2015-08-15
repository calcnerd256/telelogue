from django.views.generic import (
    TemplateView,
    CreateView,
    ListView,
    DetailView,
    FormView,
)
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from models import ChatMessage
from forms import MessageSearchForm


class PageTitleMixin(object):
    page_title = None

    def get_context_data(self, **kwargs):
        if self.page_title is None:
            raise NotImplementedError("Specify a page_title if you use PageTitleMixin.")
        context = super(PageTitleMixin, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context


class ChatHomeView(PageTitleMixin, TemplateView):
    page_title = 'Home'
    template_name = 'chat/home.html'


class MessageCreateView(CreateView):
    model = ChatMessage

    def get_success_url(self):
        url = self.request.GET.get("next")
        if url is not None: return url
        return super(MessageCreateView, self).get_success_url()


class MessageListView(ListView):
    model = ChatMessage
    paginate_by = 20

    def get_queryset(self):
        qs = super(MessageListView, self).get_queryset()
        return qs.order_by("-timestamp")


class MessageDetailView(DetailView):
    model = ChatMessage

class MessageExportView(ListView):
    model = ChatMessage
    paginate_by = 64
    template_name = "chat/chatmessage_list.html"
    def get_template_names(self):
        fallbacks = super(MessageExportView, self).get_template_names()
        requested_name = self.kwargs.get("template", "default")
        result = ["export/chat/chatmessage_list.%s" % requested_name]
        return result + fallbacks


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


class MessageSearchView(FormView):
    form_class = MessageSearchForm
    template_name = 'chat/message_search.html'

    def __init__(self):
        super(MessageSearchView, self).__init__()
        self.qs = ChatMessage.objects.none()

    def get(self, request, *args, **kwargs):
        if 'search' in request.GET:
            self.qs = ChatMessage.objects.all() # yay monkeypatching
            substr = request.GET.get('body_substring')
            if substr: # could be ''
                self.qs = self.qs.filter(body__icontains=substr)

            self.qs = self.qs.order_by('-timestamp')
        return super(MessageSearchView, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MessageSearchView, self).get_context_data(**kwargs)
        context['qs'] = self.qs
        return context
