from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "telegram_chat_id",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("id",)

    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("phone", "telegram_chat_id")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Дополнительно", {"fields": ("email", "phone", "telegram_chat_id")}),
    )
