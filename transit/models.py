from django.db import models
from cuser.fields import CurrentUserField
from chat.models import ChatMessage

class Triple(models.Model):
    source = models.ForeignKey(ChatMessage, related_name="source_set", null=True)
    path = models.ForeignKey(ChatMessage, related_name="path_set", null=True)
    destination = models.ForeignKey(ChatMessage, related_name="destination_set", null=True)
    author = CurrentUserField(add_only=True)
    timestamp = models.DateTimeField(auto_now_add=True)
