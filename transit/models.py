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
    "type": ("mental", "zero"),
    "natural": ("zero", "type"),
}

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

    @classmethod
    def lookup_semantic(cls, name):
        if name not in lookup_semantics: return None
        semantics = lookup_semantics[name]
        if 3 == len(semantics): return semantics[2]
        source_name, path_name = semantics
        source = None
        if source_name is not None:
            source = cls.lookup_semantic(source_name)
            if source is None: return None
        path = None
        if path_name is not None:
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
        _type = cls.lookup_semantic("type")
        natural = cls.lookup_semantic("natural")
        if _type is not None and natural is not None:
            existing = cls.lookup(result, _type)
            if existing is None:
                cls(source=result, path=_type, destination=natural).save()
        return result

    @classmethod
    def set_semantic(cls, name, destination, commit=True):
        # definitely a bootstrapping helper and nothing more
        semantics = lookup_semantics[name] # fail loudly: assume name in dict
        sn, pn = semantics # fail loudly: assume not already cached
        source = cls.lookup_semantic(sn)
        if source is None and sn is not None: return None
        path = cls.lookup_semantic(pn)
        if path is None and pn is not None: return None
        result = cls(source=source, path=path, destination=destination)
        if commit: result.save()
        return result


    def current_value(self, author=NotImplemented):
        return self.lookup(self.source, self.path, author)
