from django.test import TestCase
from django.urls import reverse
from accounts.models import UserProfile

class PermissionsTest(TestCase):

    def setUp(self):
        self.consultor = UserProfile.objects.create_user(
            username="consultor",
            password="1234",
            role="consultor"
        )

    def test_consultor_no_accede_admin(self):
        self.client.login(username="consultor", password="1234")
        response = self.client.get("/admin/")
        self.assertNotEqual(response.status_code, 200)
