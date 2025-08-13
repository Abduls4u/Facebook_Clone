from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Post, PostMedia

User = get_user_model()

class PostTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_text_post(self):
        """Test creating a text post"""
        data = {
            'content': 'This is a test post',
            'privacy': 'public'
        }
        response = self.client.post('/api/posts/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.content, 'This is a test post')
        self.assertEqual(post.author, self.user)

    def test_create_post_with_image(self):
        """Test creating a post with image"""
        # Create a simple image file
        image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        data = {
            'content': 'Post with image',
            'media_files': [image],
            'privacy': 'friends'
        }
        response = self.client.post('/api/posts/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.first()
        self.assertEqual(post.media.count(), 1)
        self.assertEqual(post.post_type, 'image')

    def test_get_timeline(self):
        """Test getting timeline posts"""
        # Create some posts
        Post.objects.create(
            author=self.user,
            content='Public post',
            privacy='public'
        )
        Post.objects.create(
            author=self.user,
            content='Friends post',
            privacy='friends'
        )
        
        response = self.client.get('/api/posts/timeline/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_own_post(self):
        """Test updating own post"""
        post = Post.objects.create(
            author=self.user,
            content='Original content'
        )
        
        data = {'content': 'Updated content'}
        response = self.client.patch(f'/api/posts/{post.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.content, 'Updated content')

    def test_cannot_update_others_post(self):
        """Test cannot update another user's post"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        post = Post.objects.create(
            author=other_user,
            content='Other user post'
        )
        
        data = {'content': 'Hacked content'}
        response = self.client.patch(f'/api/posts/{post.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_post(self):
        """Test deleting own post"""
        post = Post.objects.create(
            author=self.user,
            content='Post to delete'
        )
        
        response = self.client.delete(f'/api/posts/{post.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        post.refresh_from_db()
        self.assertTrue(post.is_deleted)

    def test_get_my_posts(self):
        """Test getting user's own posts"""
        # Create posts for current user and another user
        Post.objects.create(author=self.user, content='My post 1')
        Post.objects.create(author=self.user, content='My post 2')
        
        other_user = User.objects.create_user(
            username='other', email='other@example.com', password='pass'
        )
        Post.objects.create(author=other_user, content='Other post')
        
        response = self.client.get('/api/posts/my_posts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for post in response.data:
            self.assertEqual(post['author']['username'], self.user.username)