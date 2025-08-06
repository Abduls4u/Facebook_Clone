from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    """ 
    Serializer for user profiles
    """
    full_name = serializers.ReadOnlyField()
    friends_count = serializers.SerializerMethodField()
    mutual_friends_count = serializers.SerializerMethodField()
    friendship_status = serializers.SerializerMethodField()


    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'bio', 'profile_picture', 'cover_photo', 'date_of_birth',
            'location', 'work', 'education', 'website',
            'friends_count', 'mutual_friends_count', 'friendship_status',
            'is_verified', 'is_online', 'last_seen', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'is_verified', 'created_at']
        
        def get_friends_count(self, obj):
            return Friendship.get_friends(obj).count()

        def get_mutual_friends_count(self, obj):
            request = self.context.get('request')
            if request and request.user.is_authenticated and request.user != obj:
                return len(Friendship.get_mutual_friends(request.user, obj))
            return 0

        def get_friendship_status(self, obj):
            request = self.context.get('request')
            if request and request.user.is_authenticated and request.user != obj:
                try:
                    friendship = Friendship.objects.get(
                        models.Q(requester=request.user, addressee=obj) |
                        models.Q(requester=obj, addressee=request.user)
                    )
                    return {
                        'status': friendship.status,
                        'requester': friendship.requester.username,
                        'created_at': friendship.created_at
                    }
                except Friendship.DoesNotExist:
                    return None
            return None

class UserSearchSerializer(serializers.ModelSerializer):
    """Lighter serializer for user search results"""
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'profile_picture',
            'location', 'is_verified'
        ]