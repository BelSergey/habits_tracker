# habits/validators.py
from rest_framework import serializers

MAX_DURATION_SECONDS = 120
MAX_PERIODICITY_DAYS = 7


class RewardOrRelatedHabitValidator:
    """Нельзя одновременно указать вознаграждение и связанную привычку."""
    def __call__(self, attrs):
        if attrs.get('reward') and attrs.get('related_habit'):
            raise serializers.ValidationError(
                'Нельзя одновременно указать вознаграждение и связанную привычку.'
            )


class DurationValidator:
    """Время выполнения не больше 120 секунд."""
    def __call__(self, attrs):
        duration = attrs.get('duration')
        if duration is not None and duration > MAX_DURATION_SECONDS:
            raise serializers.ValidationError(
                f'Время выполнения не может превышать {MAX_DURATION_SECONDS} секунд.'
            )


class RelatedHabitMustBePleasantValidator:
    """В связанные — только приятные привычки."""
    def __call__(self, attrs):
        related = attrs.get('related_habit')
        if related and not related.is_pleasant:
            raise serializers.ValidationError(
                'В связанные привычки можно выбирать только приятные привычки.'
            )


class PleasantHabitValidator:
    """У приятной привычки не может быть награды/связанной привычки."""
    def __call__(self, attrs):
        if attrs.get('is_pleasant') and (attrs.get('reward') or attrs.get('related_habit')):
            raise serializers.ValidationError(
                'У приятной привычки не может быть вознаграждения или связанной привычки.'
            )


class PeriodicityValidator:
    """От 1 до 7 дней."""
    def __call__(self, attrs):
        periodicity = attrs.get('periodicity')
        if periodicity is not None and (periodicity > MAX_PERIODICITY_DAYS or periodicity < 1):
            raise serializers.ValidationError(
                f'Периодичность должна быть от 1 до {MAX_PERIODICITY_DAYS} дней.'
            )