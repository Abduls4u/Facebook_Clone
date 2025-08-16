from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'post', 'content_preview', 'parent', 'created_at']
    list_filter = ['created_at', 'is_deleted']
    search_fields = ['author__username', 'content', 'post__content']
    raw_id_fields = ['post', 'author', 'parent']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    content_preview.short_description = 'Content'
