from django.db import models
from cuser.fields import CurrentUserField
from chat.models import ChatMessage

def cache_getter(getter):
    cache = {}
    def result(*args, **kwargs):
        if "cache" not in cache:
            cache["cache"] = getter(*args, **kwargs)
        return cache["cache"]
    return result


class Triple(models.Model):
    source = models.ForeignKey(ChatMessage, related_name="source_set", null=True, blank=True)
    path = models.ForeignKey(ChatMessage, related_name="path_set", null=True, blank=True)
    destination = models.ForeignKey(ChatMessage, related_name="destination_set", null=True, blank=True)
    author = CurrentUserField(add_only=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # TODO: manager method
    @classmethod
    def lookup(cls, source, path, author=NotImplemented):
        triples = cls.objects.filter(source=source, path=path).order_by("-timestamp")
        if author is not NotImplemented:
            triples = triples.filter(author=author)
        if not triples: return None
        return triples[0].destination

    def current_value(self, author=NotImplemented):
        return self.lookup(self.source, self.path, author)
