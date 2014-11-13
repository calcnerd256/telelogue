from django.db import models
from cuser.fields import CurrentUserField


class ChatMessage(models.Model):
    body = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    author = CurrentUserField(add_only=True)
