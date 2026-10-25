from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import ClientForm, MailingForm, MessageForm
from .models import Attempt, Client, Mailing, Message


def is_manager(user):
    return user.is_superuser or user.groups.filter(name='Менеджеры').exists()


# ========== Главная страница ==========
class HomeView(TemplateView):
    template_name = 'mailing/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cache_key = f'home_stats_{user.pk}'
        stats = cache.get(cache_key)
        if stats is None:
            now = timezone.now()
            if is_manager(user):
                mailings = Mailing.objects.all()
                attempts = Attempt.objects.all()
                recipients = Client.objects.all()
            else:
                mailings = Mailing.objects.filter(owner=user)
                attempts = Attempt.objects.filter(mailing__owner=user)
                recipients = Client.objects.filter(owner=user)
            stats = {
                'total_mailings': mailings.count(),
                'active_mailings': mailings.filter(
                    start_time__lte=now, end_time__gte=now
                ).count(),
                'total_recipients': recipients.count(),
                'successful_attempts': attempts.filter(status='success').count(),
                'failed_attempts': attempts.filter(status='failed').count(),
                'total_sent_messages': attempts.filter(status='success').count(),
            }
            cache.set(cache_key, stats, 300)
        context.update(stats)
        return context


# ========== CRUD для клиентов ==========
class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'mailing/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        if is_manager(self.request.user):
            return Client.objects.all()
        return Client.objects.filter(owner=self.request.user)


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('mailing:client_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('mailing:client_list')

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user or self.request.user.is_superuser


class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Client
    template_name = 'mailing/client_confirm_delete.html'
    success_url = reverse_lazy('mailing:client_list')

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user or self.request.user.is_superuser


# ========== CRUD для сообщений ==========
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'messages'

    def get_queryset(self):
        if is_manager(self.request.user):
            return Message.objects.all()
        return Message.objects.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user or self.request.user.is_superuser


class MessageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user or self.request.user.is_superuser


# ========== CRUD для рассылок ==========
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        if is_manager(self.request.user):
            queryset = Mailing.objects.all()
        else:
            queryset = Mailing.objects.filter(owner=self.request.user)
        for mailing in queryset:
            mailing.update_status()
        return queryset


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = 'mailing/mailing_detail.html'
    context_object_name = 'mailing'

    def get_queryset(self):
        if is_manager(self.request.user):
            return Mailing.objects.all()
        return Mailing.objects.filter(owner=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def test_func(self):
        obj = self.get_object()
        # Редактировать может только владелец или суперпользователь
        return obj.owner == self.request.user or self.request.user.is_superuser


class MailingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def test_func(self):
        obj = self.get_object()
        # Удалять может только владелец или суперпользователь
        return obj.owner == self.request.user or self.request.user.is_superuser


# ========== Отправка рассылки ==========
def send_mailing(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    if not (request.user.is_superuser or mailing.owner == request.user):
        messages.error(request, 'У вас нет прав на отправку этой рассылки.')
        return redirect('mailing:mailing_list')

    now = timezone.now()
    if not (mailing.start_time <= now <= mailing.end_time):
        messages.error(request, 'Отправка невозможна: текущее время вне разрешённого интервала.')
        return redirect('mailing:mailing_list')

    attempts = []
    for client in mailing.recipients.all():
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email='noreply@example.com',
                recipient_list=[client.email],
                fail_silently=False,
            )
            attempts.append(Attempt(mailing=mailing, status='success', server_response='OK'))
        except Exception as e:
            attempts.append(Attempt(mailing=mailing, status='failed', server_response=str(e)))

    Attempt.objects.bulk_create(attempts)
    messages.success(request, f'Рассылка #{mailing.pk} выполнена. Создано попыток: {len(attempts)}.')
    return redirect('mailing:mailing_list')


# ========== Просмотр попыток ==========
class AttemptListView(LoginRequiredMixin, ListView):
    model = Attempt
    template_name = 'mailing/attempt_list.html'
    context_object_name = 'attempts'

    def get_queryset(self):
        if is_manager(self.request.user):
            return Attempt.objects.all()
        return Attempt.objects.filter(mailing__owner=self.request.user)
