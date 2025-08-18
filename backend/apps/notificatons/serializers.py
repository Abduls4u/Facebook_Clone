from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from .models import Notification, NotificationPreference
from apps.users.serializers import UserListSerializer

class NotificationSerializer(serializers.Serializer):
    """Serializer for notifications"""
    sender = UserListSerializer(read_only=True)
    recipient = UserListSerializer(read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    time_since = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'sender', 'notification_type', 'title', 
            'message', 'content_type', 'content_type_name', 'object_id', 
            'extra_data', 'is_read', 'is_seen', 'created_at', 'updated_at',
            'time_since'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_time_since(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'recipient', 'sender', 'notification_type', 'title', 
            'message', 'content_type', 'object_id', 'extra_data'
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'email_post_likes', 'email_comments', 
            'email_friend_requests', 'email_mentions', 'push_post_likes', 
            'push_comments', 'push_friend_requests', 'push_mentions',
            'inapp_post_likes', 'inapp_comments', 'inapp_friend_requests', 
            'inapp_mentions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
