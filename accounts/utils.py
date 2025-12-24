from django.utils import timezone
from datetime import timedelta
from .models import PasswordResetToken

def create_reset_token(user):
    return PasswordResetToken.objects.create(user=user, expires_at=timezone.now() + timedelta(hours=1))

#cria um token que expira em 1 hora