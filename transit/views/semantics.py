from chat.views import MessageListView

from ..models import (
    FailSilently,
    Triple,
    Listify,
)

from .base import (
    EnhancedViewMixin,
    super_then,
)


class UnmetSemanticsView(EnhancedViewMixin, MessageListView):
    template_name = "transit/unmet_semantics.html"
    page_title = "Semantic Frontier"

    @FailSilently
    def get_candidate(self, name):
        try:
            Triple.edges.lookup_semantic(name)
            return
        except SilentLookupFailure:
            pass
        result = {"name": name}
        row = Triple.semantics[name]
        for k, name in zip("source path".split(" "), row):
            result[k] = {
                "name": name,
                "value": Triple.edges.lookup_semantic(name)
            }
        return result

    @Listify
    def get_candidates(self):
        for name in Triple.semantics.keys():
            candidate = self.get_candidate(name)
            if candidate is not None:
                yield candidate

    @super_then(lambda: UnmetSemanticsView)
    def get_context_data(self, context):
        context["semantic_fringe"] = self.get_candidates()

