from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone

User = get_user_model()

class NotificationType(models.TextChoices):
    POST_LIKE = 'post_like', 'Post Like'
    POST_COMMENT = 'post_comment', 'Post Comment'
    POST_SHARE = 'post_share', 'Post Share'
    FRIEND_REQUEST = 'friend_request', 'Friend Request'
    FRIEND_ACCEPT = 'friend_accept', 'Friend Accept'
    COMMENT_LIKE = 'comment_like', 'Comment Like'
    COMMENT_REPLY = 'comment_reply', 'Comment Reply'
    MENTION = 'mention', 'Mention'
    BIRTHDAY = 'birthday', 'Birthday'
    EVENT_INVITE = 'event_invite', 'Event Invite'

class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        null=True,
        blank=True
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    # Generic foreign key for linking to any model (Post, Comment, etc)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Additional data stored as JSON
    extra_data = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False)
    is_seen = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read', 'updated_at'])
    
    def mark_as_seen(self):
        self.is_seen = True
        self.save(update_fields=['is_seen', 'updated_at'])


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Email notificatons
    # Email notifications
    email_post_likes = models.BooleanField(default=True)
    email_comments = models.BooleanField(default=True)
    email_friend_requests = models.BooleanField(default=True)
    email_mentions = models.BooleanField(default=True)
    
    # Push notifications
    push_post_likes = models.BooleanField(default=True)
    push_comments = models.BooleanField(default=True)
    push_friend_requests = models.BooleanField(default=True)
    push_mentions = models.BooleanField(default=True)
    
    # In-app notifications
    inapp_post_likes = models.BooleanField(default=True)
    inapp_comments = models.BooleanField(default=True)
    inapp_friend_requests = models.BooleanField(default=True)
    inapp_mentions = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"