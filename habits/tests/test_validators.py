from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from habits.models import Habit
from habits.validators import (
    DurationValidator,
    PeriodicityValidator,
    PleasantHabitValidator,
    RelatedHabitMustBePleasantValidator,
    RewardOrRelatedHabitValidator,
)

User = get_user_model()


class ValidatorsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='oleg', email='oleg@example.com', password='pass12345'
        )
        self.pleasant_habit = Habit.objects.create(
            user=self.user, place='дом', time='20:00', action='принять ванну',
            is_pleasant=True, duration=60,
        )

    def test_reward_or_related_habit_validator_raises(self):
        validator = RewardOrRelatedHabitValidator()
        with self.assertRaises(ValidationError):
            validator({'reward': 'десерт', 'related_habit': self.pleasant_habit})

    def test_reward_or_related_habit_validator_passes(self):
        RewardOrRelatedHabitValidator()({'reward': 'десерт', 'related_habit': None})

    def test_duration_validator_raises(self):
        with self.assertRaises(ValidationError):
            DurationValidator()({'duration': 121})

    def test_duration_validator_passes(self):
        DurationValidator()({'duration': 120})

    def test_related_habit_must_be_pleasant_validator_raises(self):
        not_pleasant = Habit.objects.create(
            user=self.user, place='офис', time='09:00', action='читать', duration=60
        )
        with self.assertRaises(ValidationError):
            RelatedHabitMustBePleasantValidator()({'related_habit': not_pleasant})

    def test_related_habit_must_be_pleasant_validator_passes(self):
        RelatedHabitMustBePleasantValidator()({'related_habit': self.pleasant_habit})

    def test_pleasant_habit_validator_raises_with_reward(self):
        with self.assertRaises(ValidationError):
            PleasantHabitValidator()({'is_pleasant': True, 'reward': 'десерт'})

    def test_pleasant_habit_validator_raises_with_related(self):
        with self.assertRaises(ValidationError):
            PleasantHabitValidator()({'is_pleasant': True, 'related_habit': self.pleasant_habit})

    def test_pleasant_habit_validator_passes(self):
        PleasantHabitValidator()({'is_pleasant': True, 'reward': None, 'related_habit': None})

    def test_periodicity_validator_raises_too_big(self):
        with self.assertRaises(ValidationError):
            PeriodicityValidator()({'periodicity': 8})

    def test_periodicity_validator_raises_too_small(self):
        with self.assertRaises(ValidationError):
            PeriodicityValidator()({'periodicity': 0})

    def test_periodicity_validator_passes(self):
        PeriodicityValidator()({'periodicity': 7})