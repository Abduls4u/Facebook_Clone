from rest_framework import serializers
from .models import Post, PostMedia, PostTag
from apps.users.serializers import UserListSerializer
from apps.likes.models import Like
from django.contrib.contenttypes.models import ContentType
from apps.comments.models import Comment


class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ['id', 'media_type', 'file', 'caption', 'order']


class PostTagSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    
    class Meta:
        model = PostTag
        fields = ['user']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for reading posts"""
    author = UserListSerializer(read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)
    tags = PostTagSerializer(many=True, read_only=True)

    # Add like status fields
    user_has_liked = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    # Add recent comments (first 3)
    recent_comments = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'post_type', 'privacy',
            'location', 'media', 'tags', 'likes_count', 
            'comments_count', 'user_has_liked', 'user_reaction' 
            'recent_comments','created_at', 'updated_at'
        ]


    def get_recent_comments(self, obj):
        """Get first 3 comments"""
        from apps.comments.serializers import CommentSerializer
        recent = obj.comments.filter(is_deleted=False)[:3]
        return CommentSerializer(recent, many=True, context=self.context).data

    def get_user_has_liked(self,obj):
        """Check if current user has liked this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Post)
            return Like.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id
            ).exists()
        return False
    
    def get_user_reaction(self, obj):
        """Get current user's reaction to this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Post)
            try:
                like = like.objects.get(
                    user=request.user,
                    content_type=content_type,
                    object_id=obj.id
                )
                return like.reaction_type
            except Like.DoesNotExist:
                return None
        return None
        

class CreatePostSerializer(serializers.ModelSerializer):
    """Serializer for creating posts"""
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    tagged_users = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Post
        fields = [
            'content', 'post_type', 'privacy', 'location',
            'media_files', 'tagged_users'
        ]

    def validate_content(self, value):
        """Validate post content"""
        if not value and not self.initial_data.get('media_files'):
            raise serializers.ValidationError(
                "Post must have either content or media files"
            )
        if len(value) > 10000:
            raise serializers.ValidationError("Post content is too long")
        return value

    def validate_tagged_users(self, value):
        """Validate tagged user IDs exist"""
        if value:
            from apps.users.models import User
            existing_ids = User.objects.filter(id__in=value).values_list('id', flat=True)
            invalid_ids = set(value) - set(existing_ids)
            if invalid_ids:
                raise serializers.ValidationError(f"Invalid user IDs: {invalid_ids}")
        return value

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        tagged_users = validated_data.pop('tagged_users', [])
        
        # Set author from request
        validated_data['author'] = self.context['request'].user
        
        # Determine post type if not specified
        if not validated_data.get('post_type'):
            if media_files:
                # Simple logic: if first file is image, set as image post
                first_file = media_files[0]
                if first_file.content_type.startswith('image'):
                    validated_data['post_type'] = 'image'
                elif first_file.content_type.startswith('video'):
                    validated_data['post_type'] = 'video'
            else:
                validated_data['post_type'] = 'text'
        
        post = Post.objects.create(**validated_data)
        
        # Handle media files
        for i, media_file in enumerate(media_files):
            media_type = self._determine_media_type(media_file)
            PostMedia.objects.create(
                post=post,
                file=media_file,
                media_type=media_type,
                order=i
            )
        
        # Handle tagged users
        for user_id in tagged_users:
            try:
                from apps.users.models import User
                user = User.objects.get(id=user_id)
                PostTag.objects.create(post=post, user=user)
            except User.DoesNotExist:
                pass  # Skip invalid user IDs
        
        return post

    def _determine_media_type(self, file):
        """Determine media type based on content type"""
        content_type = file.content_type
        if content_type.startswith('image'):
            return 'image'
        elif content_type.startswith('video'):
            return 'video'
        return 'image'  # default

class UpdatePostSerializer(serializers.ModelSerializer):
    """Serializer for updating posts"""
    
    class Meta:
        model = Post
        fields = ['content', 'privacy', 'location']

    def validate_content(self, value):
        if len(value) > 10000:
            raise serializers.ValidationError("Post content is too long")
        return value