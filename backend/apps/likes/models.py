from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()

class Like(models.Model):
    """Generic like model for posts, comments, etc."""
    
    REACTION_TYPES = [
        ('like', '👍 Like'),
        ('love', '❤️ Love'),
        ('haha', '😂 Haha'),
        ('wow', '😮 Wow'),
        ('sad', '😢 Sad'),
        ('angry', '😠 Angry'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(
        max_length=10,
        choices=REACTION_TYPES,
        default='like'
    )

    # Generic foreign key to like any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(default=0)
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user']),
            models.Index(fields=['reaction_type']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.reaction_type}s {self.content_object}"