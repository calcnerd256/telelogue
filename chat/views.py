from django.views.generic import (
    TemplateView,
)


class ChatHomeView(TemplateView):
    template_name = 'chat/home.html'
