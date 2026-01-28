from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from companies.models import InsuranceCompany, EmissionRights
from invoices.models import Invoice
from policies.models import Policy


class InvoiceModelTests(TestCase):
    def setUp(self):
        self.company = InsuranceCompany.objects.create(
            name="Test Insurance Company",
            ruc="1234567890123"
        )
        self.user = UserProfile.objects.create_user(
            username="testuser",
            password="testpass123",
            role="insurance_manager"
        )
        self.policy = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            insured_value=Decimal("100000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("1000.00"),
            responsible_user=self.user,
        )
        self.today = timezone.now().date()
        self.due_date = self.today + timedelta(days=30)
        
        # Create emission rights for calculations
        EmissionRights.objects.create(
            min_amount=Decimal("0.00"),
            max_amount=Decimal("10000.00"),
            emission_right=Decimal("10.00"),
            created_by=self.user
        )

    def test_invoice_creation_with_valid_data(self):
        invoice = Invoice.objects.create(
            policy=self.policy,
            invoice_number="INV001",
            invoice_date=self.today,
            due_date=self.due_date,
            fecha_vencimiento=self.due_date,
            created_by=self.user
        )
        self.assertEqual(invoice.invoice_number, "INV001")
        self.assertEqual(invoice.policy, self.policy)
        self.assertEqual(invoice.payment_status, "pendiente")

    def test_invoice_unique_invoice_number(self):
        Invoice.objects.create(
            policy=self.policy,
            invoice_number="UNIQUE001",
            invoice_date=self.today,
            due_date=self.due_date,
            fecha_vencimiento=self.due_date,
            created_by=self.user
        )
        with self.assertRaises(Exception):  # IntegrityError
            Invoice.objects.create(
                policy=self.policy,
                invoice_number="UNIQUE001",  # Duplicate
                invoice_date=self.today,
                due_date=self.due_date,
                fecha_vencimiento=self.due_date,
                created_by=self.user
            )

    def test_calculate_invoice_amounts(self):
        invoice = Invoice(
            policy=self.policy,
            invoice_number="CALC001",
            invoice_date=self.today,
            due_date=self.due_date,
            fecha_vencimiento=self.due_date,
            created_by=self.user
        )
        invoice.calculate_amounts()
        self.assertEqual(invoice.premium, Decimal("1000.00"))
        self.assertEqual(invoice.superintendence_contribution, Decimal("35.00"))  # 3.5% of 1000
        self.assertEqual(invoice.farm_insurance_contribution, Decimal("5.00"))  # 0.5% of 1000
        self.assertEqual(invoice.emission_rights, Decimal("10.00"))  # From EmissionRights
        self.assertEqual(invoice.tax_base, Decimal("1050.00"))  # 1000 + 35 + 5 + 10
        self.assertEqual(invoice.iva, Decimal("157.50"))  # 15% of 1050
        self.assertGreater(invoice.total_amount, Decimal("1200.00"))  # Should be around 1050 + 157.50 = 1207.50

    def test_invoice_str_method(self):
        invoice = Invoice.objects.create(
            policy=self.policy,
            invoice_number="STR001",
            invoice_date=self.today,
            due_date=self.due_date,
            fecha_vencimiento=self.due_date,
            created_by=self.user
        )
        expected_str = f"Factura STR001 - {self.policy.policy_number}"
        self.assertEqual(str(invoice), expected_str)
