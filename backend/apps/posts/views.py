from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q


from .models import Post
from .serializers import PostSerializer, CreatePostSerializer, UpdatePostSerializer

class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for managing posts"""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return posts based on user's access"""
        user = self.request.user

        # For now, return all non-deleted posts
        # Later we'll filter based on friendships and privacy
        return Post.objects.filter(
            is_deleted=False,
        ).select_related('author').prefetch_related(
            'media', 'tags__user'
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePostSerializer
        elif self.action == self.action in ['update', 'partial-update']:
            return UpdatePostSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        # Only allow authors update their posts
        post = self.get_object()
        if post.author != self.request.user:
            raise PermissionDenied("You can only edit your own posts")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Soft deletes a post"""
        post = self.get_object()

        # Check if user owns the post
        if post.author != request.user:
            return Response(
                {'error': 'You can only delete your posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post.is_deleted = True
        post.save()

        return Response(
            {'message': 'Post deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def my_posts(self, request):
        """Get current user's posts"""
        posts = self.get_queryset().filter(author=request.user)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def timeline(self, request):
        """Get posts for user timeline"""
        # For now, show all public posts and user's own posts
        # Later we'll implement friend-based filtering
        posts = self.get_queryset().filter(
            Q(privacy='public') | Q(author=request.user)
        )[:20] # Limit to 20 posts

        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get detailed post view"""
        post = get_object_or_404(Post, pk=pk, is_deleted=False)
        
        # Check privacy permissions
        if not self._can_view_post(request.user, post):
            return Response(
                {'error': 'You do not have permission to view this post'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    def _can_view_post(self, user, post):
        """Check if user can view this post"""
        # Post author can always view
        if post.author == user:
            return True

        # Public posts can be viewed by anyone 
        if post.privacy == 'public':
            return True
        
        # Private post onlly by author
        if post.privacy == 'private':
            return False

        # Friends only posts - for now allow all authenticated users
        # Later we'll check actual friendship status
        if post.privacy == 'friends':
            return True
        
        return False