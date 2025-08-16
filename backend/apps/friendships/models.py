from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Friendship(models.Model):
    """Model for managing friendships between users"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('blocked', 'Blocked'),
    ]

    requester = models.ForeignKey(
        User,
        related_name='sent_friend_requests',
        on_delete=models.CASCADE
    )

    addressee = models.ForeignKey(
        User,
        related_name='received_from_requests',
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('requester', 'addressee')
        indexes = [
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['addressee', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.requester.username} -> {self.addressee.username} ({self.status})"
    
    def clean(self):
        """Validate that users can't send friend requests to themselves"""
        if self.requester == self.addressee:
            raise ValidationError("Users cannot send friend requests to themselves")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def are_friends(cls, user1, user2):
        """Checks if two users are friends"""
        return cls.objects.filter(
            models.Q(requester=user1, addressee=user2, status='accepted') | 
            models.Q(requester=user2, addressee=user1, status='accepted')
        ).exists()
    
    @classmethod
    def get_friendship(cls, user1, user2):
        """Get friendship object between two users"""
        try:
            return cls.objects.get(
                models.Q(requester=user1, addressee=user2) | 
                models.Q(requester=user2, addressee=user1)
            )
        except cls.DoesNotExist:
            return None
        
    @classmethod
    def get_friends(cls, user):
        """Get all friends of a user"""
        friend_relationships = cls.objects.filter(
            models.Q(requester=user, status='accepted') |
            models.Q(addressee=user, status='accepted')
        )
        friend_ids = set()
        for friendship in friend_relationships:
            if friendship.requester == user:
                friend_ids.add(friendship.addressee.id)
            else:
                friend_ids.add(friendship.requester.id)

        return User.objects.filter(id__in=friend_ids)
    

    @classmethod
    def get_mutual_friends(cls, user1, user2):
        """Get mutual friends between two users"""
        user1_friends = set(cls.get_friends(user1).values_list('id', flat=True))
        user2_friends = set(cls.get_friends(user2).values_list('id', flat=True))

        mutual_friend_ids = user1_friends.intersection(user2_friends)
        return User.objects.filter(id__in=mutual_friend_ids)

    @classmethod
    def get_friend_suggestions(cls, user, limit=10):
        """Get friend suggestions based on mutual friends"""
        # Get user's current friends
        current_friends = cls.get_friends(user)
        current_friends_ids = set(current_friends.values_list('id', flat=True))

        # Get friends of friends
        friends_of_friends = User.objects.filter(
            models.Q(sent_friend_requests__addressee__in=current_friends,
                     sent_friend_requests__status='accepted') | 
            models.Q(received_friend_requests__requester__in=current_friends,
                    received_friend_requests__status='accepted')
        ).exclude(
            id=user.id # Exclude self
        ).exclude(
            id__in=current_friends_ids # Exclude existing friends
        ).exclude(
            # Exclude users with existing friend requests
            models.Q(sent_friend_requests__addressee=user) |
            models.Q(received_friend_requests__requester=user)
        ).distinct()[:limit]
        
        return friends_of_friends
