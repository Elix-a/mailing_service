from django.contrib import admin

from .models import Attempt, Client, Mailing, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Настройка отображения клиентов в админке."""
    list_display = ('email', 'full_name', 'comment')
    search_fields = ('email', 'full_name')
    ordering = ('full_name',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Настройка отображения сообщений в админке."""
    list_display = ('subject', 'body')
    search_fields = ('subject', 'body')
    ordering = ('subject',)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Настройка отображения рассылок в админке."""
    list_display = ('id', 'start_time', 'end_time', 'status', 'message')
    list_filter = ('status', 'start_time', 'end_time')
    search_fields = ('message__subject',)
    filter_horizontal = ('recipients',)
    ordering = ('-start_time',)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    """Настройка отображения попыток отправки в админке."""
    list_display = ('id', 'mailing', 'attempt_time', 'status', 'server_response')
    list_filter = ('status', 'mailing')
    search_fields = ('server_response',)
    ordering = ('-attempt_time',)
