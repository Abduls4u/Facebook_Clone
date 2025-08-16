from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import Friendship
from .serializers import (
    FriendListSerializer,
    FriendRequestResponseSerializer,
    SendFriendRequestSerializer,
    FriendshipSerializer
)

from apps.users.serializers import UserListSerializer

User = get_user_model()

class FriendshipViewSet(viewsets.GenericViewSet):
    """ViewSet for managing friendships"""

    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def send_request(self, request):
        """Send a friend request"""
        serializer = SendFriendRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        target_user = serializer.validated_data['target_user']

        # Create friend request
        friendship = Friendship.objects.create(
            requester=request.user,
            addressee=target_user,
            status='pending'
        )

        # TODO: Send notification to target user

        return Response({
            'message': f"Friend request sent to {target_user.username}",
            'friendship': FriendshipSerializer(friendship).data
        }, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to a friend request"""
        friendship = get_object_or_404(
            Friendship, 
            id=pk, 
            addressee=request.user,
            status='pending'
        )
        
        serializer = FriendRequestResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        
        if action == 'accept':
            friendship.status = 'accepted'
            friendship.save()
            message = f'Friend request from {friendship.requester.username} accepted'
        else:  # decline
            friendship.status = 'declined'
            friendship.save()
            message = f'Friend request from {friendship.requester.username} declined'
        
        # TODO: Send notification to requester
        
        return Response({
            'message': message,
            'friendship': FriendshipSerializer(friendship).data
        })
    
    @action(detail=False, methods=['get'])
    def received_requests(self, request):
        """Get friend requests received by current user"""
        requests = Friendship.objects.filter(
            addressee=request.user,
            status='pending'
        ).order_by('-created_at')
        
        serializer = FriendshipSerializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sent_requests(self, request):
        """Get friend requests sent by current user"""
        requests = Friendship.objects.filter(
            requester=request.user,
            status='pending'
        ).order_by('-created_at')
        
        serializer = FriendshipSerializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def friends(self, request):
        """Get user's friends list"""
        friends = Friendship.get_friends(request.user)
        
        serializer = FriendListSerializer(
            friends, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def unfriend(self, request, pk=None):
        """Remove a friend"""
        friend = get_object_or_404(User, id=pk)
        
        friendship = Friendship.get_friendship(request.user, friend)
        if not friendship or friendship.status != 'accepted':
            return Response(
                {'error': 'You are not friends with this user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        friendship.delete()
        
        return Response({
            'message': f'You are no longer friends with {friend.username}'
        })

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a user"""
        user_to_block = get_object_or_404(User, id=pk)
        
        if user_to_block == request.user:
            return Response(
                {'error': 'You cannot block yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        friendship = Friendship.get_friendship(request.user, user_to_block)
        
        if friendship:
            friendship.status = 'blocked'
            friendship.requester = request.user  # Blocker becomes requester
            friendship.addressee = user_to_block
            friendship.save()
        else:
            friendship = Friendship.objects.create(
                requester=request.user,
                addressee=user_to_block,
                status='blocked'
            )
        
        return Response({
            'message': f'{user_to_block.username} has been blocked'
        })

    @action(detail=True, methods=['delete'])
    def unblock(self, request, pk=None):
        """Unblock a user"""
        user_to_unblock = get_object_or_404(User, id=pk)
        
        friendship = Friendship.objects.filter(
            requester=request.user,
            addressee=user_to_unblock,
            status='blocked'
        ).first()
        
        if not friendship:
            return Response(
                {'error': 'User is not blocked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        friendship.delete()
        
        return Response({
            'message': f'{user_to_unblock.username} has been unblocked'
        })

    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Get friend suggestions"""
        suggestions = Friendship.get_friend_suggestions(request.user)
        
        serializer = UserListSerializer(suggestions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def mutual_friends(self, request, pk=None):
        """Get mutual friends with another user"""
        other_user = get_object_or_404(User, id=pk)
        mutual_friends = Friendship.get_mutual_friends(request.user, other_user)
        
        serializer = UserListSerializer(mutual_friends, many=True)
        return Response(serializer.data)
