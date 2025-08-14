from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from .models import Like
from apps.posts.models import Post

User = get_user_model()

class LikeTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.post = Post.objects.create(
            author=self.user,
            content='Test post'
        )

    def test_like_post(self):
        """Test liking a post"""
        response = self.client.post(f'/api/like/post/{self.post.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['liked'])
        self.assertEqual(response.data['reaction'], 'like')
        
        # Check database
        self.assertTrue(
            Like.objects.filter(
                user=self.user,
                content_type=ContentType.objects.get_for_model(Post),
                object_id=self.post.id
            ).exists()
        )

    def test_unlike_post(self):
        """Test unliking a post"""
        # First like the post
        self.client.post(f'/api/like/post/{self.post.id}/')
        
        # Then unlike it
        response = self.client.post(f'/api/like/post/{self.post.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['liked'])
        self.assertIsNone(response.data['reaction'])

    def test_change_reaction(self):
        """Test changing reaction type"""
        # Like the post
        self.client.post(f'/api/like/post/{self.post.id}/')
        
        # Change to love
        data = {'reaction_type': 'love'}
        response = self.client.post(f'/api/like/post/{self.post.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['liked'])
        self.assertEqual(response.data['reaction'], 'love')

    def test_get_likes(self):
        """Test getting likes for a post"""
        # Create some likes
        Like.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(Post),
            object_id=self.post.id,
            reaction_type='like'
        )
        
        response = self.client.get(f'/api/likes/post/{self.post.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)
        self.assertIn('like', response.data['reactions'])

    def test_check_user_reaction(self):
        """Test checking user's reaction"""
        # No reaction initially
        response = self.client.get(f'/api/check/post/{self.post.id}/')
        self.assertFalse(response.data['liked'])
        
        # Like the post
        self.client.post(f'/api/like/post/{self.post.id}/')
        
        # Check again
        response = self.client.get(f'/api/check/post/{self.post.id}/')
        self.assertTrue(response.data['liked'])
        self.assertEqual(response.data['reaction'], 'like')