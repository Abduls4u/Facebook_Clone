from django.db import models
from django.contrib.auth import get_user_model
from apps.posts.models import Post

User = get_user_model()

class Comment(models.Model):
    """Comments on posts with nested reply support"""

    post = models.ForeignKey(
        Post,
        related_name='commentst',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # For nested comments
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    # Engagement
    likes_count = models.PositiveIntegerField(default=0)

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['parent']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        content_preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.author.username}: {content_preview}"
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    @property
    def replies_count(self):
        return self.replies.filter(is_deleted=False).count()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Update post comment count if this is a new comment
        if is_new and not self.is_deleted:
            self.post.comments_count = Comment.objects.filter(
                post=self.post,
                is_deleted=False
            ).count()
            self.post.save(update_fields=['comments_count'])