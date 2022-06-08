"""
Django forms
"""
from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    '''
    Form to add a comment and
    insert a sentiment
    '''
    class Meta:
        """
        Link for to model, set fields and labels
        """
        model = Comment
        fields = ('body', 'sentiment')
        labels = {
            "body": "Share your idea on this ticker",
        }


class EditForm(forms.ModelForm):
    '''
    Form to edit the body of a comment
    and change sentiment
    '''
    class Meta:
        """
        Link for to model, set fields and labels
        """
        model = Comment
        fields = ('body', 'sentiment')
        labels = {
            "body": "Post a comment:",
            "sentiment": "Change your sentiment:"
        }
