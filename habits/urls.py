from django.urls import path
from .views import HabitListCreateView, HabitRetrieveUpdateDestroyView, PublicHabitListView, telegram_webhook

app_name = 'habits'

urlpatterns = [
    path('', HabitListCreateView.as_view(), name='habit-list-create'),
    path('<int:pk>/', HabitRetrieveUpdateDestroyView.as_view(), name='habit-detail'),
    path('public/', PublicHabitListView.as_view(), name='habit-public-list'),
    path('telegram/webhook/', telegram_webhook, name='telegram-webhook'),
]