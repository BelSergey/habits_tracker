from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class TelegramWebhookTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="oleg", email="oleg@example.com", password="pass12345"
        )

    def test_webhook_binds_chat_id_to_existing_user(self):
        url = reverse("habits:telegram-webhook")
        payload = {"message": {"chat": {"id": 999, "username": "oleg"}}}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.telegram_chat_id, "999")

    def test_webhook_ignores_unknown_username(self):
        url = reverse("habits:telegram-webhook")
        payload = {"message": {"chat": {"id": 111, "username": "unknown"}}}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.telegram_chat_id)

    def test_webhook_handles_empty_payload(self):
        url = reverse("habits:telegram-webhook")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
