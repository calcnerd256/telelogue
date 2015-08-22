import warnings
from django.db import models
from django.core.urlresolvers import reverse
from cuser.fields import CurrentUserField
from chat.models import ChatMessage

from .managers import (
    EdgeManager,
    SilentLookupFailure,
    TransitManager,
    Decorum,
    FailSilently,
    ViewManager,
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
    "this telelogue": ("local", "telelogue"),
    "user here": ("this telelogue", "user"),
}
featurebag_names = [
    None,
    "tag",
    "hide",
    "reply",
    "sticky",
    "reply tag",
    "MIMEtype",
    "base64",
]
semantic_cache = {}


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
    views = ViewManager()

    semantics = lookup_semantics
    featurebag = featurebag_names
    semcache = semantic_cache

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

    def current_dict(self):
        return {
            "source": self.source,
            "path": self.path,
            "destination": self.current_value(),
        }


def patch_on(target, rename=None):
    def result(fn):
        name = rename if rename is not None else fn.__name__
        setattr(target, name, fn)
        return lambda *args, **kwargs: getattr(target, name)(*args, **kwargs)
    return result


def semantic_property(fn):
    name = fn.__name__
    @property
    @FailSilently
    def decorated(self):
        return self.semantic_cache(name, fn())
    return patch_on(ChatMessage, name)(decorated)


def cache_getter(name):
    def decorator(fn):
        def decorated(self, *args, **kwargs):
            if hasattr(self, name): return getattr(self, name)
            result = fn(self, *args, **kwargs)
            setattr(self, name, result)
            return result
        if hasattr(fn, "__name__"):
            decorated.__name__ = fn.__name__
        return decorated
    return decorator


def not_null(x):
    if x is None:
        raise SilentLookupFailure()
    return x


class EnhancedMessage(ChatMessage):

    @patch_on(ChatMessage)
    @cache_getter("_cache")
    def get_cache(self):
        return {}

    @patch_on(ChatMessage)
    def semantic_cache(self, lookup, semantic=None):
        if semantic is None: semantic = lookup
        cache = self.get_cache()
        if lookup not in cache:
            cache[lookup] = self.lookup_semantic(semantic, as_path=True)
        return cache[lookup]

    @semantic_property
    def hide():
        pass

    @semantic_property
    def sticky():
        pass

    @semantic_property
    def parent():
        return "reply"

    @patch_on(ChatMessage, "tag")
    @property
    @FailSilently
    def tag(self):
        result = self.semantic_cache("tag")
        if result is None: return result
        parent = self.parent
        if parent is None: return result
        if result == FailSilently(Triple.edges.lookup_semantic("reply_tag")):
            result.get_body_preview = lambda *args, **kwargs: "a reply"
        return result

    @patch_on(ChatMessage)
    def get_ancestors(self):
        current = self
        result = []
        while current is not None and current not in result:
            result.append(current)
            current = current.parent
        return reversed(result)

    @patch_on(ChatMessage)
    def get_previous(self):
        return ChatMessage.objects.get(pk=self.pk - 1)

    @patch_on(ChatMessage)
    def get_next(self):
        return ChatMessage.objects.get(pk=self.pk + 1)

    @patch_on(ChatMessage)
    def get_absolute_url(self):
        return reverse("transit_message_detail", kwargs={"pk": self.pk})

    @patch_on(ChatMessage)
    @FailSilently
    def get_mimetype(self):
        return not_null(self.lookup_semantic("MIMEtype")).body

    @patch_on(ChatMessage)
    def lookup_semantic(self, name, as_path=False):
        other = Triple.edges.lookup_semantic(name)
        if as_path:
            return not_null(other).lookup(self)
        return self.lookup(other)

    @patch_on(ChatMessage)
    def lookup(self, other, reverse=False):
        if reverse:
            return not_null(other).lookup(self)
        return Triple.edges.lookup(self, other)
