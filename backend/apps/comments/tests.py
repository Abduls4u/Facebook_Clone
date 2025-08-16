from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.response import Response

from .models import Comment
from apps.posts.models import Post

User = get_user_model()

class CommentTestCase(TestCase):
    """Test for comments app"""
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
            content='Test post',
        )

    def test_create_comment(self):
        """Test creating a comment"""
        data = {'content': 'This is a test comment'}
        response = self.client.post(f"/api/posts/{self.post.id}/comments/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        
        comment = Comment.objects.first()
        self.assertEqual(comment.content, 'This is a test comment')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_create_reply(self):
        """Test creating a reply to a comment"""
        # Create a parent comment
        parent_comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Parent comment'
        )

        data = {
            'content': 'This is a reply',
            'parent': parent_comment.id
        }

        response = self.client.post(f"/api/posts/{self.post.id}/comments/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        reply = Comment.objects.get(content='This is a reply')
        self.assertEqual(reply.parent, parent_comment)
        self.assertTrue(reply.is_reply)

    def test_get_comments(self):
        """Test getting comments for a post"""
        # Create some comments
        Comment.objects.create(
            post=self.post,
            author=self.user,
            content='First comment'
        )
        Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Second comment'
        )

        response = self.client.get(f"/api/posts/{self.post.id}/comments/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['count'], 2)

    def test_update_comment(self):
        """Test updating a comment"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='First comment'
        )

        data = {'content': 'Updated comment'}
        response = self.client.patch(f"/api/posts/{self.post.id}/comments/{comment.id}/", data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Updated comment')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_cannot_update_deleted_comment(self):
        """Test cannot update a deleted comment"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='First comment'
        )
        comment.is_deleted = True
        comment.save()

        data = {'content': 'Updated comment'}
        response = self.client.patch(f"/api/posts/{self.post.id}/comments/{comment.id}/", data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Ensure comment is not updated
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'Updated comment')
        self.assertEqual(comment.content, 'First comment')  
        self.assertTrue(comment.is_deleted)
        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def test_cannot_update_others_comments(self):
        """Test cannot update another user's comment"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Other user comment'
        )

        data = {'content': 'Hacked comment'}
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(
            f"/api/posts/{self.post.id}/comments/{comment.id}/",
            data
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_comment(self):
        """Test deleting a comment"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='First comment'
        )

        response = self.client.delete(f"/api/posts/{self.post.id}/comments/{comment.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)

    
    def test_get_replies(self):
        """Test getting replies to a comment"""
        parent = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Parent comment'
        )
        
        # Create replies
        Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Reply 1',
            parent=parent
        )
        Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Reply 2',
            parent=parent
        )
        
        response = self.client.get(
            f"/api/posts/{self.post.id}/comments/{parent.id}/replies/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_comment_count_update(self):
        """Test that post comment count updates correctly"""
        initial_count = self.post.comments_count
        
        # Create comment
        data = {'content': 'New comment'}
        self.client.post(f'/api/posts/{self.post.id}/comments/', data)
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.comments_count, initial_count + 1)