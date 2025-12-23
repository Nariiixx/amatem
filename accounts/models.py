from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=15, unique=True)

    coins = models.BigIntegerField(default=0)
    points = models.BigIntegerField(default=0)
    nivel = models.BigIntegerField(default=0)
    exp = models.BigIntegerField(default=0)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
