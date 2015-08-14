from django.db import models
from cuser.fields import CurrentUserField
from chat.models import ChatMessage

from .managers import (
    EdgeManager,
    SilentLookupFailure,
    TransitManager,
)


def cache_getter(getter):
    cache = {}
    def result(*args, **kwargs):
        if "cache" not in cache:
            cache["cache"] = getter(*args, **kwargs)
        return cache["cache"]
    return result


lookup_semantics = {
    "query": (None, None),
    "successor": (None, "query"),
    "root": ("successor", "query"),
    "zero": ("successor", "successor"),
    "physical": ("root", "zero"),
    "one": ("successor", "zero"),
    "mental": ("root", "one"),
    "two": ("successor", "one"),
    "social": ("root", "two"),
    "type": ("mental", "zero"),
    "natural": ("zero", "type"),
    "agent": ("social", "zero"),
    "peer": ("agent", "zero"),
    "user": ("agent", "one"),
    "nobody": ("user", "zero"),
    "superuser": ("user", "one"),
    "local": ("peer", "zero"),
    "process": ("agent", "two"),
    "transit": ("process", "zero"),
    "telelogue": ("process", "one"),
    "featurebag": ("telelogue", "one"),
    "tag": ("featurebag", "one"),
    "hide": ("featurebag", "two"),
    "three": ("successor", "two"),
    "reply": ("featurebag", "three"),
    "four": ("successor", "three"),
    "sticky": ("featurebag", "four"),
    "five": ("successor", "four"),
    "reply tag": ("featurebag", "five"),
}


def fail_silently(fn):
    def result(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except SilentLookupFailure:
            return None
    return result


def listify(fn):
    def result(*args, **kwargs):
        return list(fn(*args, **kwargs))
    return result


class Triple(models.Model):
    source = models.ForeignKey(ChatMessage, related_name="source_set", null=True, blank=True)
    path = models.ForeignKey(ChatMessage, related_name="path_set", null=True, blank=True)
    destination = models.ForeignKey(ChatMessage, related_name="destination_set", null=True, blank=True)
    author = CurrentUserField(add_only=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    edges = EdgeManager()
    util = TransitManager()

    semantics = lookup_semantics

    # TODO: use only the manager methods and deprecate the class methods
    @classmethod
    @fail_silently
    def lookup(cls, source, path, author=NotImplemented):
        return cls.edges.lookup(source, path, author)

    @classmethod
    @fail_silently
    def lookup_semantic(cls, name):
        return cls.edges.lookup_semantic(name)

    @classmethod
    @fail_silently
    def lookup_natural(cls, n, cache=NotImplemented):
        if cache is NotImplemented:
            return cls.util.lookup_natural(n)
        return cls.util.lookup_natural(n, cache)

    @classmethod
    @fail_silently
    def set_semantic(cls, name, destination, commit=True):
        return cls.edges.set_semantic(name, destination, commit)

    @classmethod
    @fail_silently
    @listify
    def get_tags(cls):
        return cls.util.get_tags()

    @fail_silently
    def current_value(self, author=NotImplemented):
        edges = self.__class__.edges
        source = self.source
        path = self.path
        return edges.lookup(source, path, author)
