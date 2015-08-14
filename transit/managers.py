from django.db import models


class SilentLookupFailure(Exception):
    pass


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
