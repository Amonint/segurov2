from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile


class AuthenticationTest(TestCase):

    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username="testuser", password="test123", role="consultor"
        )

    def test_login_correcto(self):
        login = self.client.login(username="testuser", password="test123")
        self.assertTrue(login)

    def test_login_falla_con_password_incorrecto(self):
        login = self.client.login(username="testuser", password="incorrecto")
        self.assertFalse(login)
