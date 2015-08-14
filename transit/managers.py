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
