from django.db.models import Q

from chat.views import MessageListView

from ..models import (
    FailSilently,
    Triple,
)

from .base import (
    EnhancedViewMixin,
    super_then,
)


class UntaggedMessagesView(EnhancedViewMixin, MessageListView):
    template_name = "transit/untagged_messages.html"
    page_title = "Untagged Messages"

    def get_tag(self, cascade=True):
        try:
            result = Triple.edges.lookup_semantic("tag")
            if result is not None:
                return result
            if "aggressive" == cascade:
                raise SilentFailure()
            return result
        except SilentFailure:
            if cascade:
                raise

    def get_query_filter(self, efficient=True):
        tag = self.get_tag("aggressive")
        taggings = tag.source_set.all()
        if not efficient:
            # TODO: make this fast, perhaps by inlining t.current_value()
            return ~Q(
                id__in=[
                    t.path_id
                    for t
                    in taggings
                    if t.current_value() is not None
                ]
            )
        removed = Q(
            pk__in=[
                t.path
                for t
                in taggings.filter(destination__isnull=True)
                if t.current_value() is None
            ]
        )
        never = ~Q(pk__in=taggings.values("path"))
        return removed|never

    @super_then(lambda: UntaggedMessagesView)
    @FailSilently
    def get_queryset(self, result):
        return result.filter(
            self.get_query_filter()
        ).order_by("timestamp")

    @FailSilently
    def get_tags(self):
        return list(
            Triple.util.get_tags()
        )

    @super_then(lambda: UntaggedMessagesView)
    def get_context_data(self, context):
        context.update(
            {
                "tags": self.get_tags(),
                "tag_tag": self.get_tag(False),
            }
        )
