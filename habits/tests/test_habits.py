from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from habits.models import Habit

User = get_user_model()


class HabitCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="oleg", email="oleg@example.com", password="pass12345"
        )
        self.other_user = User.objects.create_user(
            username="ivan", email="ivan@example.com", password="pass12345"
        )
        self.client.force_authenticate(self.user)

    def test_create_habit_success(self):
        url = reverse("habits:habit-list-create")
        data = {
            "place": "парк",
            "time": "07:00",
            "action": "бегать",
            "periodicity": 1,
            "duration": 60,
            "is_public": False,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        habit = Habit.objects.get(id=response.data["id"])
        self.assertEqual(habit.user, self.user)

    def test_create_habit_with_reward_and_related_fails(self):
        pleasant = Habit.objects.create(
            user=self.user,
            place="дом",
            time="20:00",
            action="ванна",
            is_pleasant=True,
            duration=60,
        )
        url = reverse("habits:habit-list-create")
        data = {
            "place": "парк",
            "time": "07:00",
            "action": "бегать",
            "periodicity": 1,
            "duration": 60,
            "reward": "десерт",
            "related_habit": pleasant.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_habit_duration_too_long_fails(self):
        url = reverse("habits:habit-list-create")
        data = {
            "place": "парк",
            "time": "07:00",
            "action": "бегать",
            "periodicity": 1,
            "duration": 200,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_habit_periodicity_too_big_fails(self):
        url = reverse("habits:habit-list-create")
        data = {
            "place": "парк",
            "time": "07:00",
            "action": "бегать",
            "periodicity": 10,
            "duration": 60,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_habit_related_not_pleasant_fails(self):
        useful = Habit.objects.create(
            user=self.user,
            place="офис",
            time="09:00",
            action="читать",
            duration=60,
        )
        url = reverse("habits:habit-list-create")
        data = {
            "place": "парк",
            "time": "07:00",
            "action": "бегать",
            "periodicity": 1,
            "duration": 60,
            "related_habit": useful.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_habit_related_habit_of_another_user_fails(self):
        foreign_pleasant = Habit.objects.create(
            user=self.other_user,
            place="дом",
            time="20:00",
            action="ванна",
            is_pleasant=True,
            duration=60,
        )
        url = reverse("habits:habit-list-create")
        data = {
            "place": "парк",
            "time": "07:00",
            "action": "бегать",
            "periodicity": 1,
            "duration": 60,
            "related_habit": foreign_pleasant.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_shows_only_own_habits(self):
        Habit.objects.create(
            user=self.user, place="дом", time="08:00", action="зарядка", duration=60
        )
        Habit.objects.create(
            user=self.other_user,
            place="дом",
            time="08:00",
            action="зарядка",
            duration=60,
        )
        url = reverse("habits:habit-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_pagination_page_size_is_five(self):
        for i in range(7):
            Habit.objects.create(
                user=self.user,
                place="дом",
                time=f"0{i % 9}:00",
                action=f"действие {i}",
                duration=60,
            )
        url = reverse("habits:habit-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertEqual(response.data["count"], 7)

    def test_retrieve_own_habit(self):
        habit = Habit.objects.create(
            user=self.user, place="дом", time="08:00", action="зарядка", duration=60
        )
        url = reverse("habits:habit-detail", args=[habit.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_retrieve_foreign_habit(self):
        habit = Habit.objects.create(
            user=self.other_user,
            place="дом",
            time="08:00",
            action="зарядка",
            duration=60,
        )
        url = reverse("habits:habit-detail", args=[habit.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_habit(self):
        habit = Habit.objects.create(
            user=self.user, place="дом", time="08:00", action="зарядка", duration=60
        )
        url = reverse("habits:habit-detail", args=[habit.id])
        response = self.client.patch(url, {"action": "йога"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        habit.refresh_from_db()
        self.assertEqual(habit.action, "йога")

    def test_cannot_update_foreign_habit(self):
        habit = Habit.objects.create(
            user=self.other_user,
            place="дом",
            time="08:00",
            action="зарядка",
            duration=60,
        )
        url = reverse("habits:habit-detail", args=[habit.id])
        response = self.client.patch(url, {"action": "йога"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_habit(self):
        habit = Habit.objects.create(
            user=self.user, place="дом", time="08:00", action="зарядка", duration=60
        )
        url = reverse("habits:habit-detail", args=[habit.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(id=habit.id).exists())

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(None)
        url = reverse("habits:habit-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PublicHabitListTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="oleg", email="oleg@example.com", password="pass12345"
        )
        self.other_user = User.objects.create_user(
            username="ivan", email="ivan@example.com", password="pass12345"
        )
        self.client.force_authenticate(self.user)

    def test_public_list_contains_only_public_habits(self):
        Habit.objects.create(
            user=self.other_user,
            place="парк",
            time="07:00",
            action="бегать",
            duration=60,
            is_public=True,
        )
        Habit.objects.create(
            user=self.other_user,
            place="дом",
            time="08:00",
            action="читать",
            duration=60,
            is_public=False,
        )
        url = reverse("habits:habit-public-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_public_habit_detail_not_accessible_for_non_owner(self):
        public_habit = Habit.objects.create(
            user=self.other_user,
            place="парк",
            time="07:00",
            action="бегать",
            duration=60,
            is_public=True,
        )
        url = reverse("habits:habit-detail", args=[public_habit.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
