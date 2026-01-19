from django.test import TestCase
from policies.models import Policy

class PolicyModelTest(TestCase):

    def test_numero_poliza_se_genera(self):
        policy = Policy.objects.create(
            # ajusta campos obligatorios
        )
        self.assertIsNotNone(policy.policy_number)
