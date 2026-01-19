from django.test import TestCase
from claims.models import Claim

class ClaimWorkflowTest(TestCase):

    def test_transicion_estado_valida(self):
        claim = Claim.objects.create(status="reportado")
        claim.status = "evaluacion"
        claim.save()

        self.assertEqual(claim.status, "evaluacion")
