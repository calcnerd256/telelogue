from chat.views import PageTitleMixin

from ..models import(
    Triple,
    FailSilently,
)


class NextOnSuccessMixin(object):
    def get_success_url(self):
        url = self.request.GET.get("next")
        if url is not None: return url
        return super(NextOnSuccessMixin, self).get_success_url()


def super_then(clsfn, name=None):
    def decoration(fn):
        method_name = fn.__name__
        if name is not None: method_name = name
        def decorated(self, *args, **kwargs):
            method = getattr(super(clsfn(), self), method_name)
            intermediate = method(*args, **kwargs)
            result = fn(self, intermediate)
            if result is None: return intermediate
            return result
        return decorated
    return decoration

