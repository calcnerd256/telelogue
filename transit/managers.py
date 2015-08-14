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
        if n == 0: return edges.lookup_semantic("zero")
        if n < 0:
            raise SilentLookupFailure()
        if n < len(cache): return cache[n]
        successor = edges.lookup_semantic("successor")
        previous = self.lookup_natural(n - 1)  # recursive
        if previous is None:
            raise SilentLookupFailure()
        if n == len(cache):
            # this will always be true by this point
            cache.append(previous)
        result = cls.edges.lookup(successor, previous)
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
