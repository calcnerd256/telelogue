import datetime
from types import MethodType

from django.db import models

from chat.models import ChatMessage


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
    def lookup_history(self, source, path, author=NotImplemented):
        history = self.filter(source=source, path=path)
        if author is not NotImplemented:
            history = history.filter(author=author)
        return history

    def lookup(self, source, path, author=NotImplemented):
        triples = self.lookup_history(source, path, author).order_by("-timestamp")
        if not triples:
            raise SilentLookupFailure()
        return triples[0].destination

    def lookup_semantic(self, name):
        if name is None: return None
        if name in self.model.semcache:
            return self.model.semcache[name]
        if name in self.model.featurebag:
            if "featurebag" == name:
                # this should not be
                raise SilentLookupFailure()
            featurebag = self.lookup_semantic("featurebag")
            n = [
                i
                for i, feat
                in enumerate(self.model.featurebag)
                if feat == name
            ][0]
            num = self.model.util.lookup_natural(n)
            destination = self.lookup(featurebag, num)
            if destination is None: return destination
            self.model.semcache[name] = destination
            return destination
        if name not in self.model.semantics:
            raise SilentLookupFailure()
        semantics = self.model.semantics[name]
        destination = self.lookup(*map(self.lookup_semantic, semantics))
        if destination is None: return destination  # don't cache deletion
        self.model.semcache[name] = destination
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

    def coerce_luser(self, user):
        n = self.lookup_natural(user.pk)
        local_users = self.model.edges.lookup_semantic("user here")
        return self.model.edges.lookup(local_users, n)

class ViewManager(models.Manager):
    def get_between_times(self, begin_time, end_time):
        result = ChatMessage.objects.filter(
            timestamp__gte=begin_time,
            timestamp__lte=end_time,
        ).order_by("-timestamp")
        for m in result:
            if not getattr(m, "hide", False):
                yield m

    def get_day(self, day):
        day_ordinal = day.toordinal()
        beginning = datetime.datetime.fromordinal(day_ordinal)
        end = datetime.datetime.fromordinal(day_ordinal + 1)
        return self.get_between_times(beginning, end)

    def get_today(self):
        # TODO: move this to a manager on ChatMessage
        today = datetime.date.today()
        one_day = datetime.timedelta(1)
        yesterday = today - one_day
        yesterday_midnight = datetime.datetime.fromordinal(yesterday.toordinal())  # there must be a better way
        tomorrow = today + one_day
        tonight_midnight = datetime.datetime.fromordinal(tomorrow.toordinal())
        return self.get_between_times(yesterday_midnight, tonight_midnight)

    def get_sticky_posts(self):
        sticky = self.model.edges.lookup_semantic("sticky")
        glue = sticky.source_set.all()
        pks = (tack.path_id for tack in glue if tack.current_value() is not None)
        result = ChatMessage.objects.filter(id__in=pks)
        return result.order_by("timestamp")

    def get_edges_incident_on(self, message, rel="source", corel="path"):
        candidates = getattr(message, "%s_set" % rel).all()
        def to_pk(edge):
            other = getattr(edge, corel)
            if other is None: return 0
            return other.pk

        def from_pk(pk):
            for edge in candidates:
                if pk == to_pk(edge):
                    return edge

        for pk in set(map(to_pk, candidates)):
            yield from_pk(pk).current_dict()
