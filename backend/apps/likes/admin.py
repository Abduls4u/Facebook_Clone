from django.contrib import admin
from .models import Like

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_object', 'reaction_type', 'created_at']
    list_filter = ['reaction_type', 'created_at', 'content_type']
    search_fields = ['user__username']
    
    def content_object(self, obj):
        return str(obj.content_object)
    content_object.short_description = 'Content'