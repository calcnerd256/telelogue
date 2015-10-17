from django.db import models
from django.core.urlresolvers import reverse
from cuser.fields import CurrentUserField


class ChatMessageExportMixin(object):
    def get_body_codepoints(self):
        u = unicode(self.body)
        return [ord(point) for point in u]

    def get_body_serial(self):
        codepoints = self.get_body_codepoints()
        hexpoints = ["%X" % n for n in codepoints]
        return " ".join(hexpoints)

    def get_body_preview(self):
        #ASCII-safe
        points = self.get_body_codepoints()
        if not points: return points
        whitelist = [c for c in " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.0123456789,-_:/"]
        code_map = {
            ord("\n"): ord(" "),
        }
        asciipoints = [
            code_map.get(p, p)
            for p
            in points
            if p < 256
        ]
        preview_chars = map(chr, asciipoints)
        safechars = [c for c in preview_chars if c in whitelist]
        return "".join(safechars[:64])


class ChatMessage(ChatMessageExportMixin, models.Model):
    body = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    author = CurrentUserField(add_only=True)

    def get_absolute_url(self):
        return reverse('message_detail', kwargs={'pk': self.pk})

    def get_author_url(self):
        author = self.author
        return reverse("user_detail", kwargs={"pk": author.pk})
