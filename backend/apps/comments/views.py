from rest_framework import  viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

from .models import Comment
from .serializers import (
    CommentSerializer,
    NestedCommentSerializer,
    UpdateCommentSerializer,
    CreateCommentSerializer
)
from apps.posts.models import Post
from apps.likes.models import Like

class CommentViewSet(viewsets.ModelViewSet):
    """Viewset for managing comments"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        if post_id:
            return Comment.objects.filter(
                post_id= post_id,
                is_deleted=False
            ).select_related('author').prefetch_related('replies')
        return Comment.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCommentSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateCommentSerializer
        elif self.action == 'list':
            return NestedCommentSerializer
        return CommentSerializer

    def list(self, request, *args, **kwargs):
        """Get top-level comments for a post"""
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id, is_deleted=False)

        # Check if user can view this post
        if not self._can_view_post(request.user, post):
            return Response(
                {'error': 'You do not have permission to view this post'},
                status=status.HTTP_403_FORBIDDEN
            )
        # Get only top-level comments (no parent)
        comments = self.get_queryset().filter(parent=None)

        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create a new comment"""
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id, is_deleted=False)

        # Check if user can comment on this post
        if not self._can_comment_on_post(request.user, post):
            return Response(
                {'error': 'You do not have permission to comment on this post'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data, context={'post': post, **self.get_serializer_context()})
        serializer.is_valid(raise_exception=True)

        # Validate parent comment belongs to same post
        parent = serializer.validated_data.get('parent')
        if parent and parent.post != post:
            return Response(
                {'error': 'Parent comment must belong to same post'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = serializer.save()

        return Response(
            CommentSerializer(comment, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a comment"""
        comment = self.get_object()

        # Check if user own the comment
        if comment.author != request.user:
            return Response(
                {'error': 'You can only edit your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return Response(
                {'error': 'You can only edit your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)


    def destroy(self, request, *args, **kwargs):
        """Soft delete a comment"""
        comment = self.get_object()

        # Check if user owns the comment
        if comment.author != request.user:
            return Response(
                {'error': 'You can only delete your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.is_deleted = True
        comment.save()

        # Update post comment count
        comment.post.comments_count = Comment.objects.filter(
            post=comment.post,
            is_deleted=False
        ).count()
        comment.post.save(update_fields=['comments_count'])

        return Response(
            {'message': 'Comment deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None, post_id=None):
        """Get replies to a specific comment"""
        comment = self.get_object()
        replies = comment.replies.filter(is_deleted=False)

        serializer = CommentSerializer(replies, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
    
    def _can_view_post(self, user, post):
        """Check if user can view this post"""
         # Same logic as in posts app
        if post.author == user:
            return True
        if post.privacy == 'public':
            return True
        if post.privacy == 'private':
            return False
        if post.privacy == 'friends':
            return True  # For now, allow all authenticated users
        return False

    def _can_comment_on_post(self, user, post):
        """Check if user can comment on this post"""
        # For now, same as view permission
        # Later we might have different rules (e.g., friends can comment but public can only view)
        return self._can_view_post(user, post)