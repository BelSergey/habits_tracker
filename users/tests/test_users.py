from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserRegistrationTests(APITestCase):
    def test_register_user_success(self):
        url = reverse('users:register')
        data = {
            'username': 'oleg',
            'email': 'oleg@example.com',
            'password': 'StrongPass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='oleg@example.com').exists())
        user = User.objects.get(email='oleg@example.com')
        self.assertTrue(user.check_password('StrongPass123'))

    def test_register_user_duplicate_email_fails(self):
        User.objects.create_user(username='u1', email='dup@example.com', password='StrongPass123')
        url = reverse('users:register')
        data = {'username': 'u2', 'email': 'dup@example.com', 'password': 'StrongPass123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_weak_password_fails(self):
        url = reverse('users:register')
        data = {'username': 'u3', 'email': 'weak@example.com', 'password': '123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='oleg', email='oleg@example.com', password='StrongPass123'
        )

    def test_login_success(self):
        url = reverse('users:login')
        response = self.client.post(
            url, {'email': 'oleg@example.com', 'password': 'StrongPass123'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password_fails(self):
        url = reverse('users:login')
        response = self.client.post(url, {'email': 'oleg@example.com', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        login_url = reverse('users:login')
        login_response = self.client.post(
            login_url, {'email': 'oleg@example.com', 'password': 'StrongPass123'}
        )
        refresh_token = login_response.data['refresh']

        refresh_url = reverse('users:login-refresh')
        response = self.client.post(refresh_url, {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_profile_requires_authentication(self):
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_retrieve_and_update(self):
        self.client.force_authenticate(self.user)
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'oleg@example.com')

        response = self.client.patch(url, {'telegram_chat_id': '12345'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.telegram_chat_id, '12345')

    def test_profile_cannot_change_email(self):
        self.client.force_authenticate(self.user)
        url = reverse('users:profile')
        response = self.client.patch(url, {'email': 'new@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        # email доступен только на чтение — значение не должно измениться
        self.assertEqual(self.user.email, 'oleg@example.com')