from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Friendship
from apps.users.serializers import UserListSerializer

User = get_user_model()

class FriendshipSerializer(serializers.ModelSerializer):
    """Serializer for friendship objects"""

    requester = UserListSerializer(read_only=True)
    addressee = UserListSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = [
            'id', 'requester', 'addressee', 'status',
            'created_at', 'updated_at'
        ]

class SendFriendRequestSerializer(serializers.Serializer):
    """Serializer for sending friend requests"""
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")

    def validate(self, attrs):
        request_user = self.context['request'].user
        target_user = attrs['user_id']

        # Can't send request to self
        if request_user == target_user:
            raise serializers.ValidationError(
                "You cannot send a friend request to yourself"
            )
        
        # Check if friendship already exists
        existing_friendship = Friendship.get_friendship(request_user, target_user)
        if existing_friendship:
            if existing_friendship.status == 'pending':
                raise serializers.ValidationError(
                    "Friend request already pending"
                )
            elif existing_friendship.status == 'accepted':
                raise serializers.ValidationError(
                    "You are already friends with this user"
                )
            elif existing_friendship.status == 'blocked':
                raise serializers.ValidationError(
                    "Cannot send friend request to this user"
                )
        
        attrs['target_user'] = target_user
        return attrs


class FriendRequestResponseSerializer(serializers.Serializer):
    """Serializer for responding to friend requests"""
    action = serializers.ChoiceField(choices=['accept', 'decline'])


class FriendListSerializer(serializers.ModelSerializer):
    """Serialize for listing friends"""
    mutual_friends_count = serializers.SerializerMethodField()
    friendship_date = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'profile_picture', 
            'location', 'is_verified', 'mutual_friends_count',
            'friendship_date'
        ]

    def get_mutual_friends_count(self, obj):
        request_user = self.context['request'].user
        return len(Friendship.get_mutual_friends(request_user, obj))
    
    def get_friendship_date(self, obj):
        request_user = self.context['request'].user
        friendship = Friendship.get_friendship(request_user, obj)
        if friendship and friendship.status == 'accepted':
            return friendship.updated_at
        return None
    