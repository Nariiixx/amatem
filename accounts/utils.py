import logging

from django.core.mail import EmailMessage
from django.utils import timezone
from datetime import timedelta

from .models import PasswordResetToken

logger = logging.getLogger(__name__)


def create_reset_token(user):
    """Cria um token de reset de senha que expira em 1 hora."""
    return PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=1)
    )


def send_email_notification(subject, body, to_email):
    """Envia email e loga falhas sem quebrar o fluxo da view."""
    try:
        EmailMessage(subject, body, to=[to_email]).send()
        return True
    except Exception as e:
        logger.error(f"Falha ao enviar email para {to_email}: {e}")
        return False