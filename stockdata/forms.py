from .models import Comment
from django import forms


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body', 'sentiment')

class EditForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body', 'sentiment')
        labels = {
            "body": "Post a comment:",
            "sentiment": "Change your sentiment:"
        }