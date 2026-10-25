from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Настройка отображения кастомного пользователя в админке."""
    model = CustomUser
    list_display = ('email', 'full_name', 'email_verified', 'is_staff', 'is_active')
    list_filter = ('email_verified', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name')
    ordering = ('email',)

    # Настройки формы редактирования (убираем username)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('full_name',)}),
        ('Права доступа', {'fields': ('email_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    # Настройки формы добавления (убираем username)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    