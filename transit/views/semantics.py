from chat.views import MessageListView

from ..models import (
    FailSilently,
    Triple,
    Listify,
    SilentLookupFailure,
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
        if name in Triple.featurebag:
            result["source"] = {
                "name": "featurebag",
                "value": Triple.edges.lookup_semantic("featurebag")
            }
            n = [i for i, feat in enumerate(Triple.featurebag) if feat == name][0]
            result["path"] = {
                "name": n,
                "value": Triple.util.lookup_natural(n)
            }
            return result
        row = Triple.semantics[name]
        for k, name in zip("source path".split(" "), row):
            result[k] = {
                "name": name,
                "value": Triple.edges.lookup_semantic(name)
            }
        return result

    @FailSilently
    def get_numeric_fringe(self):
        zero = Triple.edges.lookup_semantic("zero")
        succ = Triple.edges.lookup_semantic("successor")
        n = 0
        visited = []
        current = zero
        while current not in visited:
            visited.append(current)
            try:
                current = Triple.edges.lookup(succ, current)
                if current in visited: return None
                n += 1
            except SilentLookupFailure:
                pass
        return {
            "name": n+1,
            "source": {
                "name": "successor",
                "value": succ
            },
            "path": {
                "name": n,
                "value": current
            }
        }

    @Listify
    def get_candidates(self):
        names = Triple.semantics.keys() + Triple.featurebag[1:]
        for name in names:
            candidate = self.get_candidate(name)
            if candidate is not None:
                yield candidate
        next_number = self.get_numeric_fringe()
        if next_number is not None:
            yield next_number

    @super_then(lambda: UnmetSemanticsView)
    def get_context_data(self, context):
        context["semantic_fringe"] = self.get_candidates()

