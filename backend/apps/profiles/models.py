from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Friendship(models.model):
    """Model for managing friendships between users"""


    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('blocked', 'Blocked'),
    ]

    sent_from = models.ForeignKey(
        User,
        related_name="sent_friend_requests",
        on_delete=models.CASCADE
    )

    sent_to =  models.ForeignKey(
        User,
        related_name='received_friend_requests',
        on_delete=models.CASCADE
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sent_from', 'sent_to')
        indexes = [
            models.Index(fields=['sent_from', 'status']),
            models.Index(fields=['sent_to', 'status'])
        ]

    def __str__(self):
        return f"{self.sent_from.username} -> {self.sent_to.username} ({self.status})"

    @classmethod
    def are_friends(cls, user1, user2):
        """Check if two users are friends"""
        return cls.objects.filter(
            models.Q(sent_from=user1, sent_to=user2, status='accepted') |
            models.Q(sent_from=user1, sent_to=user1, status='accepted')
        ).exists()
    
    @classmethod
    def get_mutual_friends(cls, user1, user2):
        """Get mutual friends between two users"""
        user1_friends = cls.get_friends(user1)
        user2_friends = cls.get_friends(user2)
        return user1_friends.intersection(user2_friends)
    

    @classmethod
    def get_friends(cls, user):
        """Get all friends of a user"""
        friends_ids = cls.objects.filter(
            models.Q(sent_from=user, status='accepted') |
            models.Q(sent_to=user, status='accepted')
        ).values_list('sent_from', 'sent_to')

        friends = set()
        for sent_from_id, sent_to_id in friends_ids:
            if sent_from_id == user.id:
                friends.add(sent_to_id)
            else:
                friends.add(sent_from_id)

        return User.objects.filter(id__in=friends)