from django.db import models
from django.core.urlresolvers import reverse
from cuser.fields import CurrentUserField


class ChatMessage(models.Model):
    body = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    author = CurrentUserField(add_only=True)

    def get_absolute_url(self):
        return reverse('message_detail', kwargs={'pk': self.pk})
