from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from brokers.models import Broker
from companies.models import InsuranceCompany
from policies.models import Policy, PolicyDocument


class PolicyModelTests(TestCase):
    def setUp(self):
        self.company = InsuranceCompany.objects.create(
            name="Test Insurance Company",
            ruc="1234567890123"
        )
        self.broker = Broker.objects.create(
            name="Test Broker",
            ruc="9876543210987",
            commission_percentage=Decimal("5.00")
        )
        self.user = UserProfile.objects.create_user(
            username="testuser",
            password="testpass123",
            role="insurance_manager"
        )
        self.today = timezone.now().date()
        self.next_year = self.today + timedelta(days=365)

    def test_policy_creation_with_valid_data(self):
        policy = Policy.objects.create(
            insurance_company=self.company,
            broker=self.broker,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=self.next_year,
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
            responsible_user=self.user,
        )
        self.assertIsNotNone(policy.policy_number)
        self.assertEqual(policy.status, "active")
        self.assertEqual(policy.insurance_company, self.company)

    def test_policy_number_generation(self):
        policy1 = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=self.next_year,
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
        )
        policy2 = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=self.next_year,
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
        )
        self.assertNotEqual(policy1.policy_number, policy2.policy_number)
        self.assertTrue(policy1.policy_number.startswith("POL-"))
        self.assertTrue(policy2.policy_number.startswith("POL-"))

    def test_calcular_valores_fiscales(self):
        policy = Policy(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=self.next_year,
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("1000.00"),
        )
        policy.calcular_valores_fiscales()
        self.assertEqual(policy.contrib_superintendencia, Decimal("35.00"))  # 3.5%
        self.assertEqual(policy.contrib_seguro_campesino, Decimal("5.00"))   # 0.5%
        # Other calculations depend on EmissionRights

    def test_policy_validation_invalid_dates(self):
        policy = Policy(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.next_year,
            end_date=self.today,  # End before start
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
        )
        with self.assertRaises(ValidationError):
            policy.full_clean()

    def test_policy_validation_zero_prima(self):
        policy = Policy(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=self.next_year,
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("0.00"),
        )
        with self.assertRaises(ValidationError):
            policy.full_clean()

    def test_policy_validation_zero_insured_value(self):
        policy = Policy(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=self.next_year,
            insured_value=Decimal("0.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
        )
        with self.assertRaises(ValidationError):
            policy.full_clean()

    def test_is_expiring_soon(self):
        # Policy expiring in 15 days
        expiring_soon_date = self.today + timedelta(days=15)
        policy = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=expiring_soon_date,
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
        )
        self.assertTrue(policy.is_expiring_soon(30))
        self.assertFalse(policy.is_expiring_soon(10))

    def test_policy_str_method(self):
        policy = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=self.next_year,
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
        )
        expected_str = f"{policy.policy_number} - {self.company.name}"
        self.assertEqual(str(policy), expected_str)


class PolicyDocumentModelTests(TestCase):
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
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
            responsible_user=self.user,
        )

    def test_document_creation(self):
        from django.core.files.base import ContentFile
        document = PolicyDocument.objects.create(
            policy=self.policy,
            document_name="Test Policy Document",
            document_type="policy",
            file=ContentFile(b"test content", name="test.pdf"),
            file_size=12,
            mime_type="application/pdf",
            uploaded_by=self.user
        )
        self.assertEqual(document.version, 1)
        self.assertTrue(document.is_latest_version)
        self.assertEqual(document.policy, self.policy)
