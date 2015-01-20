# Create your views here.

from django.views.generic import (
    TemplateView,
)
from .models import (
    lookup_semantics,
    Triple,
)
from chat.models import ChatMessage
from chat.views import MessageListView

class UnmetSemanticsView(MessageListView):
    template_name = "transit/unmet_semantics.html"

    def get_candidates(self):
        def filter_step(name):
            if Triple.lookup_semantic(name) is not None: return False
            source_name, path_name = lookup_semantics[name][0:2]
            if source_name is not None:
                if Triple.lookup_semantic(source_name) is None:
                    return False
            if path_name is not None:
                if Triple.lookup_semantic(path_name) is None:
                    return False
            return True
        def map_step(name):
            source_name, path_name = lookup_semantics[name][0:2]
            source = {
                "name": source_name,
                "value": Triple.lookup_semantic(source_name),
            }
            path = {
                "name": path_name,
                "value": Triple.lookup_semantic(path_name),
            }
            return {
                "name": name,
                "source": source,
                "path": path,
            }
        return [map_step(name) for name in lookup_semantics.keys() if filter_step(name)]


    def get_context_data(self, *args, **kwargs):
        context = super(UnmetSemanticsView, self).get_context_data(*args, **kwargs)
        context["semantic_fringe"] = self.get_candidates()
        return context
