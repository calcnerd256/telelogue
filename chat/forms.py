from django import forms


class MessageSearchForm(forms.Form):
    body_substring = forms.CharField(max_length=256)
