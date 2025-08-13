from django.contrib import admin
from .models import Post, PostMedia, PostTag

class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 0

class PostTagInline(admin.TabularInline):
    model = PostTag
    extra = 0

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'content_preview', 'post_type', 'privacy', 'created_at']
    list_filter = ['post_type', 'privacy', 'created_at']
    search_fields = ['author__username', 'content']
    inlines = [PostMediaInline, PostTagInline]
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'media_type', 'file', 'order']
    list_filter = ['media_type', 'created_at']