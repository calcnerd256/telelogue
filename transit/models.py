from django.db import models
from cuser.fields import CurrentUserField
from chat.models import ChatMessage

from .managers import (
    EdgeManager,
    SilentLookupFailure,
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

    # TODO: manager methods
    @classmethod
    @fail_silently
    def lookup(cls, source, path, author=NotImplemented):
        return cls.edges.lookup(source, path, author)

    @classmethod
    @fail_silently
    def lookup_semantic(cls, name):
        if name not in lookup_semantics:
            raise SilentLookupFailure()
        semantics = lookup_semantics[name]
        if 3 == len(semantics): return semantics[2]
        source_name, path_name = semantics
        source = None
        if source_name is not None:
            source = cls.lookup_semantic(source_name)
            if source is None:
                raise SilentLookupFailure()
        path = None
        if path_name is not None:
            path = cls.lookup_semantic(path_name)
            if path is None:
                raise SilentLookupFailure()
        destination = cls.edges.lookup(source, path)
        # previously, deletion led to failure; now, deletion stores None in the cache
        with_cache = (source_name, path_name, destination)
        lookup_semantics[name] = with_cache
        return destination

    @classmethod
    @fail_silently
    def lookup_natural(cls, n, cache=[]):
        n = int(n) # try me
        if n == 0: return cls.lookup_semantic("zero")
        if n < 0:
            raise SilentLookupFailure()
        if n < len(cache): return cache[n]
        successor = cls.lookup_semantic("successor")
        if successor is None:
            raise SilentLookupFailure()
        previous = cls.lookup_natural(n - 1) # recursive
        if previous is None:
            raise SilentLookupFailure()
        if n == len(cache): cache.append(previous)
        result = cls.lookup(successor, previous)
        _type = cls.lookup_semantic("type")
        natural = cls.lookup_semantic("natural")
        if _type is not None and natural is not None:
            try:
                cls.edges.lookup(result, _type)
            except SilentLookupFailure:
                cls(source=result, path=_type, destination=natural).save()
        return result

    @classmethod
    @fail_silently
    def set_semantic(cls, name, destination, commit=True):
        # definitely a bootstrapping helper and nothing more
        semantics = lookup_semantics[name] # fail loudly: assume name in dict
        sn, pn = semantics # fail loudly: assume not already cached
        source = cls.lookup_semantic(sn)
        if source is None and sn is not None:
            raise SilentLookupFailure()
        path = cls.lookup_semantic(pn)
        if path is None and pn is not None:
            raise SilentLookupFailure()
        result = cls(source=source, path=path, destination=destination)
        if commit: result.save()
        return result

    @classmethod
    @fail_silently
    @listify
    def get_tags(cls):
        tag = cls.lookup_semantic("tag")
        if tag is None:
            raise SilentLookupFailure()
        for t in cls.objects.filter(source=tag, destination=tag):
            try:
                if cls.edges.lookup(tag, t.path) == tag:
                    yield t.path
            except SilentLookupFailure:
                pass


    @fail_silently
    def current_value(self, author=NotImplemented):
        return Triple.edges.lookup(self.source, self.path, author)
