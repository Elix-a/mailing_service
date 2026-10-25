from django.conf import settings
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CustomAuthenticationForm, UserRegisterForm
from .models import CustomUser


class RegisterView(CreateView):
    """Представление для регистрации нового пользователя."""
    model = CustomUser
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:email_verification_sent')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object

        # Формируем ссылку для подтверждения email
        verify_link = self.request.build_absolute_uri(
            f'/users/verify/{user.verification_token}/'
        )

        # Отправляем письмо с подтверждением
        send_mail(
            subject='Подтверждение email',
            message=(
                f'Здравствуйте, {user.full_name or user.email}!\n\n'
                f'Для подтверждения вашего email перейдите по ссылке:\n'
                f'{verify_link}\n\n'
                f'Если вы не регистрировались на сайте, просто проигнорируйте это письмо.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return response


def verify_email(request, token):
    """Подтверждение email по токену."""
    try:
        user = CustomUser.objects.get(verification_token=token)
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=['email_verified'])
        return render(request, 'users/email_verified.html')
    except CustomUser.DoesNotExist:
        return render(request, 'users/email_verification_failed.html')


class CustomLoginView(LoginView):
    """Представление для входа по email."""
    form_class = CustomAuthenticationForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True
