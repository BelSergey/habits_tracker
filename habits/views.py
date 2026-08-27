from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import Habit
from .paginators import HabitPagination
from .permissions import IsOwner
from .serializers import HabitSerializer, PublicHabitSerializer

User = get_user_model()


class HabitListCreateView(generics.ListCreateAPIView):
    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = HabitPagination

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HabitRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwner)

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    queryset = Habit.objects.filter(is_public=True)
    serializer_class = PublicHabitSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = HabitPagination


@extend_schema(
    summary='Webhook Telegram-бота',
    description=(
        'Принимает update от Telegram Bot API. Если пользователь отправил '
        'боту команду /start и его username совпадает с зарегистрированным '
        'в системе, сохраняет telegram_chat_id для рассылки напоминаний.'
    ),
    request={
        'application/json': {
            'example': {'message': {'chat': {'id': 123456789, 'username': 'oleg'}}}
        }
    },
    responses={200: OpenApiExample('OK', value={'ok': True})},
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def telegram_webhook(request):
    message = request.data.get("message", {})
    chat = message.get("chat", {})
    chat_id, username = chat.get("id"), chat.get("username")
    if chat_id and username:
        User.objects.filter(username=username).update(telegram_chat_id=str(chat_id))
    return Response({"ok": True})
