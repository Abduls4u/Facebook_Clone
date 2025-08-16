from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Comment
from apps.users.serializers import UserListSerializer
from apps.likes.models import Like

class CommentSerializer(serializers.ModelSerializer):
    """Serializer for reading comments"""
    author = UserListSerializer(read_only=True)
    replies_count = serializers.ReadOnlyField()
    user_has_liked = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'content', 'parent', 'likes_count',
            'replies_count', 'user_has_liked', 'user_reaction',
            'created_at', 'updated_at'
        ]

    def get_user_has_liked(self, obj):
        """Check if the current user has liked this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Comment)
            return Like.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id
            ).exists()
        return False
    
    def get_user_reaction(self, obj):
        """Gets current user's reaction to this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Comment)
            try:
                like = Like.objects.get(
                    user=request.user,
                    content_type=content_type,
                    object_id=obj.id
                )
                return like.reaction_type
            except Like.DoesNotExist:
                return None
        return None
    
class NestedCommentSerializer(serializers.ModelSerializer):
    """Serializer for comments with their replies"""
    replies = serializers.SerializerMethodField()
    author = UserListSerializer(read_only=True)
    replies_count = serializers.ReadOnlyField()
    user_has_liked = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    class Meta():
        model = Comment
        fields = [
            'id', 'author', 'content', 'parent', 'likes_count',
            'replies_count', 'replies', 'user_has_liked', 
            'user_reaction', 'created_at', 'updated_at'
        ]   
    
    def get_replies(self, obj):
        if obj.replies.filter(is_deleted=False).exists():
            replies = obj.replies.filter(is_deleted=False)[:5] # Limit replies
            return CommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def get_user_has_liked(self, obj):
        """Check if the current user has liked this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Comment)
            return Like.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id
            ).exists()
        return False

    def get_user_reaction(self, obj):
        """Gets current user's reaction to this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Comment)
            try:
                like = Like.objects.get(
                    user=request.user,
                    content_type=content_type,
                    object_id=obj.id
                )
                return like.reaction_type
            except Like.DoesNotExist:
                return None
        return None


class CreateCommentSerializer(serializers.ModelSerializer):
    """Serializer for creating comments"""

    class Meta:
        model = Comment
        fields = ['content', 'parent']

    def validate_content(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError('Comment cannot be empty')
        if len(value) > 1000:
            raise serializers.ValidationError('Comment is too long')
        return value.strip()

    def validate_parent(self, value):
        """Validate if parent exists and belongs to same post"""
        if value:
            # Check if parent comment exists and not deleted
            if value.is_deleted:
                raise serializers.ValidationError('Cannot reply to a deleted comment')
            # For now, we'll set the post in the view
            # Later we can validate parent belongs to same post
        return value
    
    def create(self, validated_data):
        # Set author and post from context
        validated_data['author'] = self.context['request'].user
        validated_data['post'] = self.context['post']
        return super().create(validated_data)


class UpdateCommentSerializer(serializers.ModelSerializer):
    """Serializer for updating comments"""

    class Meta:
        model = Comment
        fields = ['content']

    def validate_content(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Comment cannot be empty")
        if len(value) > 1000:
            raise serializers.ValidationError("Comment is too long")
        return value.strip()