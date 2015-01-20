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
}

class Triple(models.Model):
    source = models.ForeignKey(ChatMessage, related_name="source_set", null=True)
    path = models.ForeignKey(ChatMessage, related_name="path_set", null=True)
    destination = models.ForeignKey(ChatMessage, related_name="destination_set", null=True)
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

    @classmethod
    def lookup_semantic(cls, name):
        if name not in lookup_semantics: return None
        semantics = lookup_semantics[name]
        if 3 == len(semantics): return semantics[2]
        source_name, path_name = semantics
        if source_name is None:
            source = None
        else:
            source = cls.lookup_semantic(source_name)
            if source is None: return None
        if path_name is None:
            path = None
        else:
            path = cls.lookup_semantic(path_name)
            if path is None: return None
        destination = cls.lookup(source, path)
        if destination is None: return None
        with_cache = (source_name, path_name, destination)
        lookup_semantics[name] = with_cache
        return destination

    @classmethod
    def lookup_natural(cls, n, cache=[]):
        n = int(n) # try me
        if n == 0: return cls.lookup_semantic("zero")
        if n < 0: return None
        if n < len(cache): return cache[n]
        successor = cls.lookup_semantic("successor")
        if successor is None: return None
        previous = cls.lookup_natural(n - 1) # recursive
        if previous is None: return None
        if n == len(cache): cache.append(previous)
        result = cls.lookup(successor, previous)
        return result
