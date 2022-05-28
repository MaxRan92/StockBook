from django.contrib import admin
from .models import Comment, StockInfo
from django_summernote.admin import SummernoteModelAdmin

@admin.register(StockInfo)
class StockInfoAdmin(SummernoteModelAdmin):
    # add the stock models to the admin panel
    # apply summernote to the content text field
    # prepopulate slug with title, add filter, listdisplay, search functionality

    list_display = ('title', 'slug', 'bulls', 'bears', 'status', 'created_on')
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('status', 'created_on')
    summernote_fields = ('description')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'body', 'sentiment', 'stock', 'created_on', 'approved')
    list_filter = ('approved', 'created_on')
    search_fields = ('name', 'email', 'body')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
