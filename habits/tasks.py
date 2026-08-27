
from celery import shared_task
from django.utils import timezone
from .models import Habit
from .services import send_telegram_message


@shared_task
def send_habit_reminders():
    now = timezone.localtime()
    current_time = now.time().replace(second=0, microsecond=0)

    habits = Habit.objects.filter(
        time__hour=current_time.hour,
        time__minute=current_time.minute,
        is_pleasant=False,
        user__telegram_chat_id__isnull=False,
    ).exclude(user__telegram_chat_id='')

    sent = 0
    for habit in habits:
        days_since_created = (now.date() - habit.created_at.date()).days
        if days_since_created % habit.periodicity != 0:
            continue
        message = f'Напоминание: я буду {habit.action} в {habit.time.strftime("%H:%M")} в {habit.place}.'
        if habit.reward:
            message += f'\nВознаграждение: {habit.reward}'
        elif habit.related_habit:
            message += f'\nПосле — приятная привычка: {habit.related_habit.action}'
        send_telegram_message(habit.user.telegram_chat_id, message)
        sent += 1
    return sent