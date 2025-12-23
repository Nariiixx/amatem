from django.test import TestCase
from django.urls import reverse
from .models import CustomUser

class AuthTests(TestCase):

    def test_user_cannot_login_without_activation(self):
        user = CustomUser.objects.create_user(
            username='teste',
            email='teste@email.com',
            password='123456',
            is_active=False
        )

        login = self.client.login(username='teste', password='123456')
        self.assertFalse(login)

    def test_user_activation(self):
        user = CustomUser.objects.create_user(
            username='teste2',
            email='teste2@email.com',
            password='123456',
            is_active=True
        )

        login = self.client.login(username='teste2', password='123456')
        self.assertTrue(login)
