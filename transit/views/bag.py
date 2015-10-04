from django.views.generic import CreateView

from ..models import Triple

from .base import EnhancedMessageMixin

class CreateBagView(EnhancedMessageMixin, CreateView):
    template_name = "chat/form.html"

    def form_valid(self, form):
        response = super(CreateBagView, self).form_valid(form)
        new_bag = self.object
        current_baglike = self.get_bag()
        old_bag = current_baglike["bag"]
        Triple(source=new_bag, path=old_bag, destination=old_bag).save()
        new_contents = [Triple(source=new_bag, path=item, destination=old_bag) for item in current_baglike["contents"]]
        for trip in new_contents: trip.save()
        Triple(source=old_bag, path=new_bag, destination=new_bag).save()
        me = Triple.util.coerce_luser(self.request.user)
        bag = Triple.edges.lookup_semantic("bag")
        Triple(source=me, path=bag, destination=new_bag).save()
        return response
