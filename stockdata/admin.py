"""
Django admin interface set up
"""

from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Comment, StockInfo


@admin.register(StockInfo)
class StockInfoAdmin(SummernoteModelAdmin):
    '''
    Add the stock models to the admin panel
    apply summernote to the description text field
    prepopulate slug with title, add filter, listdisplay,
    search functionality
    '''

    list_display = ('title', 'slug', 'status', 'created_on')
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('status', 'created_on')
    summernote_fields = ('description')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    '''
    Add the comment models to the admin panel
    apply summernote to the comment text field
    add approved/not approved filters and serach
    functionalities
    '''
    list_display = ('name', 'body', 'sentiment', 'stock',
                    'created_on', 'approved')
    list_filter = ('approved', 'created_on')
    search_fields = ('name', 'email', 'body')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        '''
        Give the admin the possibility to approve
        comments
        '''
        queryset.update(approved=True)
