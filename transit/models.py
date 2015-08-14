from types import MethodType
import warnings
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


class Listify(Decorum):
    composer = list
    def after_call(self, *args, **kwargs):
        return self.composer(*args, **kwargs)


class Deprecate(Decorum):
    message = "deprecated"
    category = DeprecationWarning
    def warn(self, *args, **kwargs):
        warnings.warn(self.message, self.category, *args, **kwargs)

    def before_call(self, *args, **kwargs):
        self.warn()
        return super(Deprecate, self).before_call(*args, **kwargs)


class ClassMethod(Decorum):
    cls = None

    def call(self, fn, args, *arfs, **kwargs):
        return super(ClassMethod, self).call(fn, [self.cls] + list(args), *arfs, **kwargs)

    def __get__(self, obj, cls=None):
        self.cls = cls
        if self.cls is None: self.cls = type(obj)
        return self


class Managed(ClassMethod, FailSilently, Deprecate):
    pass


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

    @Managed
    def lookup(cls, source, path, author=NotImplemented):
        return cls.edges.lookup(source, path, author)

    @Managed
    def lookup_semantic(cls, name):
        return cls.edges.lookup_semantic(name)

    @Managed
    def lookup_natural(cls, n, cache=NotImplemented):
        if cache is NotImplemented:
            return cls.util.lookup_natural(n)
        return cls.util.lookup_natural(n, cache)

    @Managed
    def set_semantic(cls, name, destination, commit=True):
        return cls.edges.set_semantic(name, destination, commit)

    @Managed
    @Listify
    def get_tags(cls):
        return cls.util.get_tags()

    @FailSilently
    def current_value(self, author=NotImplemented):
        edges = self.__class__.edges
        source = self.source
        path = self.path
        return edges.lookup(source, path, author)
