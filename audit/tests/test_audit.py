from django.test import TestCase
from django.contrib.auth import get_user_model
from audit.models import AuditLog

User = get_user_model()

class AuditTest(TestCase):

    def test_se_crea_log(self):
        user = User.objects.create_user(
            username="auditor",
            password="1234"
        )

        self.client.login(username="auditor", password="1234")
        self.client.get("/")  # acción cualquiera

        self.assertTrue(AuditLog.objects.exists())
