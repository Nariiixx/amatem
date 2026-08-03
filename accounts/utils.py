from asyncio.log import logger
from email.message import EmailMessage


from django.utils import timezone
from datetime import timedelta
from .models import PasswordResetToken

def create_reset_token(user):
    return PasswordResetToken.objects.create(user=user, expires_at=timezone.now() + timedelta(hours=1))

#cria um token que expira em 1 hora
def send_email_notification(subject, body, to_email):
    try:
        EmailMessage(subject, body, to=[to_email]).send()
    except Exception as e:
        logger.error (f"falha ao enviar email para {to_email}: {e}")