from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'password', 'phone', 'telegram_chat_id')
    list_filter = ('id', 'username', )

