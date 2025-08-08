from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.reverse import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        """Test if user can register successfully"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

        url = reverse('users:register')
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_user_login(self):
        """Test if user can log in successfully"""
        # Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        url = reverse('users:login')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)

    def test_profile_update(self):
        """Test if user can update their profile"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )

        self.client.force_authenticate(user=user)

        data = {
            'bio': "Updated bio",
            'location': 'New York'
        }

        url = reverse('users:profile')
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.bio, 'Updated bio')
        self.assertEqual(user.location, 'New York')

    def test_logout(self):
        """Tests if a user can logout successfully"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )

        self.client.force_authenticate(user=user)


        url = reverse('users:logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

