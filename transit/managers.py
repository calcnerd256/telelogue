from types import MethodType
from django.db import models


class SilentLookupFailure(Exception):
    pass


class Decorum(object):
    decorated = None
    def __init__(self, decorated):
        self.decorated = decorated

    __get__ = MethodType

    def before_call(self, *args, **kwargs):
        return self.decorated, args, kwargs

    def after_call(self, result):
        return result

    def call(self, fn, args, kwargs):
        return fn(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.after_call(
            self.call(
                *self.before_call(
                    *args,
                    **kwargs
                )
            )
        )

    @property
    def __name__(self):
        return self.decorated.__name__


class FailSilently(Decorum):
    failure_class = SilentLookupFailure
    default_value = None
    def call(self, *args, **kwargs):
        try:
            return super(FailSilently, self).call(*args, **kwargs)
        except Exception as e:
            if not isinstance(e, self.failure_class):
                raise
            return self.default_value


class EdgeManager(models.Manager):
    def lookup(self, source, path, author=NotImplemented):
        triples = self.filter(source=source, path=path).order_by("-timestamp")
        if author is not NotImplemented:
            triples = triples.filter(author=author)
        if not triples:
            raise SilentLookupFailure()
        return triples[0].destination

    def lookup_semantic(self, name):
        if name is None: return None
        if name not in self.model.semantics:
            raise SilentLookupFailure()
        semantics = self.model.semantics[name]
        if 3 == len(semantics): return semantics[2]
        destination = self.lookup(*map(self.lookup_semantic, semantics))
        # previously, deletion led to failure; now, deletion stores None in the cache
        with_cache = tuple(list(semantics) + [destination])
        self.model.semantics[name] = with_cache
        return destination

    def set_semantic(self, name, destination, commit=True):
        # definitely a bootstrapping helper and nothing more
        source, path = map(  # fail loudly: assume not already cached
            self.lookup_semantic,
            self.model.semantics[name]  # fail loudly: assume name in dict
        )
        result = self.model(source=source, path=path, destination=destination)
        if commit: result.save()
        return result


class TransitManager(models.Manager):
    def get_tags(self):
        edges = self.model.edges
        tag = edges.lookup_semantic("tag")
        for t in self.filter(source=tag, destination=tag):
            try:
                path = t.path
                if edges.lookup(tag, path) == tag:
                    yield path
            except SilentLookupFailure:
                pass

    def lookup_natural(self, n, cache=[]):
        n = int(n)  # just try me; I dare you
        edges = self.model.edges
        if n < 0:
            raise SilentLookupFailure()
        if n < len(cache): return cache[n]
        if 0 == n:
            cache.append(edges.lookup_semantic("zero"))
            return cache[n]
        successor = edges.lookup_semantic("successor")
        previous = self.lookup_natural(n - 1)  # recursive
        if previous is None:
            raise SilentLookupFailure()
        result = edges.lookup(successor, previous)
        if n == len(cache):
            # this will always be true by this point
            cache.append(result)
        # the above used to fail silently, but now it cascades its failure
        try:
            _type = edges.lookup_semantic("type")
            natural = edges.lookup_semantic("natural")
            try:
                edges.lookup(result, _type)
            except SilentLookupFailure:
                self.model(source=result, path=_type, destination=natural).save()
        except SilentLookupFailure:
            pass
        return result
