from rest_framework import serializers
from .models import Habit
from .validators import (
    DurationValidator, PeriodicityValidator, PleasantHabitValidator,
    RelatedHabitMustBePleasantValidator, RewardOrRelatedHabitValidator,
)


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = ('id', 'user', 'place', 'time', 'action', 'is_pleasant',
                  'related_habit', 'periodicity', 'reward', 'duration',
                  'is_public', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
        validators = [
            RewardOrRelatedHabitValidator(),
            DurationValidator(),
            RelatedHabitMustBePleasantValidator(),
            PleasantHabitValidator(),
            PeriodicityValidator(),
        ]

    def validate_related_habit(self, value):
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError('Нельзя привязать чужую привычку.')
        return value


class PublicHabitSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Habit
        fields = ('id', 'owner', 'place', 'time', 'action', 'is_pleasant',
                  'related_habit', 'periodicity', 'reward', 'duration')
        read_only_fields = fields