from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from .models import Like
from .serializers import LikeSerializer, ReactionSerializer
from apps.posts.models import Post

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_like(request, content_type, object_id):
    """Toggle like on any object (post, comment, etc.)"""

    # Get content type
    try:
        ct = ContentType.objects.get(model=content_type)
    except ContentType.DoesNotExist:
        return Response(
            {'error': 'Invalid content type'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get the object being liked
    try:
        obj = ct.get_object_for_this_type(id=object_id)
    except ct.model_class().DoesNotExist:
        return Response(
            {'error': 'Object not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if object is deleted (for posts)
    if hasattr(obj, 'is_deleted') and obj.is_deleted:
        return Response(
            {'error': 'Cannot like deleted content'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = ReactionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    reaction_type = serializer.validated_data['reaction_type']

    # Check if user already reacted
    like, created = Like.objects.get_or_create(
        user=request.user,
        content_type=ct,
        object_id=object_id,
        defaults={'reaction_type': reaction_type}
    )

    if not created:
        if like.reaction_type == reaction_type:
            # Same reaction - remove it (unlike)
            like.delete()
            liked = False
            reaction = None
        else:
            # Different reaction - update it
            like.reaction_type = reaction_type
            like.save()
            liked = True
            reaction = reaction_type
    else:
        # New reaction
        liked = True
        reaction = reaction_type

    # Update counts for posts
    if isinstance(obj, Post):
        obj.like_count = Like.objects.filter(
            content_type=ct,
            object_id=obj.id
        ).count()
        obj.save(update_fields=['likes_count'])

    return Response({
        'liked': liked,
        'reaction': reaction,
        'likes_count': getattr(obj, 'likes_count', 0)
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_likes(request, content_type, object_id):
    """Get all likes for an object"""

    try:
        ct = ContentType.objects.get(model=content_type)
    except ContentType.DoesNotExist:
        return Response(
            {'error': 'Invalid content type'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    likes = Like.objects.filter(
        content_type=ct,
        object_id=object_id,
    ).select_related('user').order_by('-created_at')

    # Group by reaction type
    reactions = {}
    for like in likes:
        if like.reaction_type not in reactions:
            reactions[like.reaction_type] = []
            reactions[like.reaction_type].append(LikeSerializer(like).data)

    return Response({
        'reactions': reactions,
        'total_count': likes.count()
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_user_reaction(request, content_type, object_id):
    """Check if current user has reacted to an object"""

    try: 
        ct = ContentType.objects.get(model=content_type)
    except ContentType.DoesNotExist:
        return Response(
            {'error': 'Invalid content type'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        like = Like.objects.get(
            user=request.user,
            content_type=ct,
            object_id=object_id
        )
        return Response({
            'liked': True,
            'reaction': like.reaction_type
        })
    except Like.DoesNotExist:
        return Response({
            'liked': False,
            'reaction': None
        })