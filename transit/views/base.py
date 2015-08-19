from django.views.generic.list import ListView
from django.views.generic.detail import models
from django.shortcuts import get_object_or_404

from chat.views import PageTitleMixin
from chat.models import ChatMessage

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


class EnhancedViewMixin(PageTitleMixin, NextOnSuccessMixin):
    @super_then(lambda: EnhancedViewMixin)
    def get_context_data(self, context):
        context["this_page"] = self.request.path
        for k in "hide sticky".split(" "):
            context["%s_pk" % k] = getattr(
                FailSilently(
                    Triple.edges.lookup_semantic
                )(k),
                "pk",
                None
            )


class EnhancedMessageMixin(EnhancedViewMixin):
    model = ChatMessage


class ObjectAndListView(ListView):
    pk_url_kwarg = "pk"

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model,
            pk=int(self.kwargs.get(self.pk_url_kwarg))
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object_list = self.get_queryset()
        context = self.get_context_data(
            object=self.object,
            object_list=self.object_list,
            **kwargs
        )
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context = {}
        obj = self.object
        context_object_name = None
        if isinstance(obj, models.Model):
            if self.object._deferred:
                obj = obj._meta.proxy_for_model
            context_object_name = obj._meta.object_name.lower()
        if context_object_name:
            context[context_object_name] = self.object
        context.update(**kwargs)
        return super(ObjectAndListView, self).get_context_data(*args, **context)


def fail_with(fallback):
    class result(FailSilently):
        default_value = fallback
    return result
