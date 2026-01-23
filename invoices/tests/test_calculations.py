from django.test import TestCase

from invoices.models import Invoice


class InvoiceCalculationTest(TestCase):

    def test_calculo_iva(self):
        invoice = Invoice.objects.create(subtotal=100)
        self.assertEqual(invoice.iva, 15)
