from django.test import TestCase
from claims.models import Claim

class ClaimModelTest(TestCase):

    def test_claim_number_autogenerado(self):
        claim = Claim.objects.create(
            # completa campos obligatorios
        )
        self.assertIsNotNone(claim.claim_number)
