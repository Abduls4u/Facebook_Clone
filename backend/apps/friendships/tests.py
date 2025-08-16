from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import Friendship

User = get_user_model()

class FriendshipTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.target_user = User.objects.create_user(
            username='targetuser',
            email='target@example.com',
            password='testpass123'
        )

    def test_send_friend_request(self):
        """Test sending a friend request"""
        response = self.client.post('/api/friends/send_request/', {
            'user_id': self.target_user.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('friendship', response.data)
        # Check database
        friendship = Friendship.objects.get(
            requester=self.user,
            addressee=self.target_user,
            status='pending'
        )
        self.assertIsNotNone(friendship)
        self.assertEqual(friendship.requester, self.user)
        self.assertEqual(friendship.addressee, self.target_user)
        self.assertEqual(friendship.status, 'pending')

    def test_respond_to_friend_request(self):
        """Test responding to a friend request"""
        # First, send a friend request
        friendship = Friendship.objects.create(
            requester=self.target_user,
            addressee=self.user,
            status='pending'
        )
        response = self.client.post(f'/api/friends/{friendship.id}/respond/', {
            'action': 'accept'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        # Check database
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')

    def test_respond_to_nonexistent_request(self):      
        """Test responding to a non-existent friend request"""
        response = self.client.post('/api/friends/999/respond/', {
            'action': 'accept'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'No Friendship matches the given query.')
        
    def test_send_request_to_self(self):
        """Test sending a friend request to oneself"""
        response = self.client.post('/api/friends/send_request/', {
            'user_id': self.user.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertIn('You cannot send a friend request to yourself', response.data['non_field_errors'][0])

    def test_get_received_requests(self):
        """Test getting received friend requests"""
        # Create a friend request
        Friendship.objects.create(
            requester=self.target_user,
            addressee=self.user,
            status='pending'
        )
        response = self.client.get('/api/friends/received_requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        request_data = response.data[0]
        self.assertEqual(request_data['requester']['username'], self.target_user.username)
        self.assertEqual(request_data['status'], 'pending')

    def test_get_friends(self):
        """Test getting friends of a user"""
        # Create a friendship
        Friendship.objects.create(
            requester=self.user,
            addressee=self.target_user,
            status='accepted'
        )
        response = self.client.get('/api/friends/friends/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        friend_data = response.data[0]
        self.assertEqual(friend_data['username'], self.target_user.username)

    def test_get_mutual_friends(self):

        """Test getting mutual friends between two users"""
        # Create friendships
        mutual_friend = User.objects.create_user(
            username='mutualfriend',
            password='testpassword'
        )
        Friendship.objects.create(
            requester=self.user,
            addressee=mutual_friend,
            status='accepted'
        )
        Friendship.objects.create(
            requester=mutual_friend,
            addressee=self.user,
            status='accepted'
        )

        response = self.client.get(f'/api/friends/{self.user.id}/mutual_friends/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        mutual_friend_data = response.data[0]
        self.assertEqual(mutual_friend_data['username'], mutual_friend.username)