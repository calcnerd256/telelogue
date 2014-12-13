from django import forms


class MessageSearchForm(forms.Form):
    search_string = forms.CharField(max_length=256)
