from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """
    Extended user model with facebook-like features
    """

    # Profile Information
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        default='profile_pics/default.jpg'
    )
    cover_photo = models.ImageField(
        upload_to='cover_photo/',
        null=True,
        blank=True,
        default='cover_photo/default.jpg'
    )

    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    work = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=100, blank=True)


    # Privacy Settings
    profile_visibility = models.CharField(
        max_length=20,
        choices= [
            ('public', 'Public'),
            ('private', 'Private'),
            ('friends', 'Friends Only'),
        ],
        default='friends'
    )

    # Account Status
    is_online = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now())

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    # Extra details
    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"

    @property
    def full_name(self):
        return f"({self.first_name} {self.last_name})".strip()

    @property
    def mutual_friends_count(self):
        pass


    