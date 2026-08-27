from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from habits.models import Habit
from habits.services import send_telegram_message
from habits.tasks import send_habit_reminders

User = get_user_model()


class TelegramServiceTests(TestCase):
    @override_settings(TELEGRAM_BOT_TOKEN="")
    def test_send_message_skipped_without_token(self):
        with patch("habits.services.requests.post") as mock_post:
            send_telegram_message("123", "hello")
            mock_post.assert_not_called()

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    def test_send_message_skipped_without_chat_id(self):
        with patch("habits.services.requests.post") as mock_post:
            send_telegram_message("", "hello")
            mock_post.assert_not_called()

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    def test_send_message_calls_api(self):
        with patch("habits.services.requests.post") as mock_post:
            send_telegram_message("123", "hello")
            mock_post.assert_called_once()


class SendHabitRemindersTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="oleg",
            email="oleg@example.com",
            password="pass12345",
            telegram_chat_id="555",
        )
        self.now = timezone.localtime()

    @patch("habits.tasks.send_telegram_message")
    def test_sends_reminder_for_matching_habit(self, mock_send):
        habit = Habit.objects.create(
            user=self.user,
            place="дом",
            time=self.now.time().replace(second=0, microsecond=0),
            action="зарядка",
            duration=60,
            periodicity=1,
        )
        habit.created_at = self.now
        habit.save(update_fields=["created_at"])

        sent_count = send_habit_reminders()

        self.assertEqual(sent_count, 1)
        mock_send.assert_called_once()

    @patch("habits.tasks.send_telegram_message")
    def test_skips_users_without_chat_id(self, mock_send):
        self.user.telegram_chat_id = ""
        self.user.save()
        Habit.objects.create(
            user=self.user,
            place="дом",
            time=self.now.time().replace(second=0, microsecond=0),
            action="зарядка",
            duration=60,
        )
        sent_count = send_habit_reminders()
        self.assertEqual(sent_count, 0)
        mock_send.assert_not_called()

    @patch("habits.tasks.send_telegram_message")
    def test_skips_pleasant_habits(self, mock_send):
        Habit.objects.create(
            user=self.user,
            place="дом",
            time=self.now.time().replace(second=0, microsecond=0),
            action="ванна",
            duration=60,
            is_pleasant=True,
        )
        sent_count = send_habit_reminders()
        self.assertEqual(sent_count, 0)
        mock_send.assert_not_called()

    @patch("habits.tasks.send_telegram_message")
    def test_skips_habit_when_time_does_not_match(self, mock_send):
        other_time = (
            (self.now + timezone.timedelta(hours=3))
            .time()
            .replace(second=0, microsecond=0)
        )
        Habit.objects.create(
            user=self.user,
            place="дом",
            time=other_time,
            action="зарядка",
            duration=60,
        )
        sent_count = send_habit_reminders()
        self.assertEqual(sent_count, 0)
        mock_send.assert_not_called()
