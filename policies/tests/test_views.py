from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile


class PolicyViewsTest(TestCase):

    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username="gerente", password="1234", role="gerente_seguros"
        )

    def test_lista_polizas_requiere_login(self):
        response = self.client.get(reverse("policy_list"))
        self.assertEqual(response.status_code, 302)

    def test_lista_polizas_autenticado(self):
        self.client.login(username="gerente", password="1234")
        response = self.client.get(reverse("policy_list"))
        self.assertEqual(response.status_code, 200)
