from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()

class Post(models.Model):
    """Manin post model"""

    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('link', 'Link'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', 'Public (Everybody)'),
        ('friends', 'Friends Only'),
        ('private', 'Only Me'),
    ]

    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField(blank=True)
    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPES,
        default='text'
    )
    privacy = models.CharField(
        max_length=30,
        choices=PRIVACY_CHOICES,
        default='friends'
    )

    # Metadata
    location = models.CharField(max_length=100, blank=True)

    # Engagement counts
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['privacy', '-created_at']),
        ]

    def __str__(self):
        content_preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.author.username}: {content_preview}"
    
    
class PostMedia(models.Model):
    """Model for post attachments (images, videos)"""

    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    post = models.ForeignKey(
        Post,
        related_name='media',
        on_delete=models.CASCADE
    )
    media_type = models.CharField(max_length=15, choices=MEDIA_TYPES)
    file = models.FileField(
        upload_to='posts/',
        validators = [
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov']
            )
        ]
    )
    caption = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.post.author.username} - {self.media_type} {self.order}"


class PostTag(models.Model):
    """Model for tagging users posts"""

    post = models.ForeignKey(
        Post,
        related_name='tags',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} tagged in {self.post.id}"
