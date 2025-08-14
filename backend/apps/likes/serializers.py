from rest_framework import serializers
from .models import Like
from apps.users.serializers import UserListSerializer

class LikeSerializer(serializers.ModelSerializer):
    """Serializer for likes"""
    user = UserListSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'reaction_type', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class ReactionSerializer(serializers.Serializer):
    """Serializer for creating reactions"""
    reaction_type = serializers.ChoiceField(
        choices=Like.REACTION_TYPES,
        default='like'
    )