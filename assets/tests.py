from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from assets.models import Asset
from companies.models import InsuranceCompany
from policies.models import Policy


class AssetModelTests(TestCase):
    def setUp(self):
        self.custodian = UserProfile.objects.create_user(
            username="custodian",
            password="testpass123",
            role="requester"
        )
        self.responsible = UserProfile.objects.create_user(
            username="responsible",
            password="testpass123",
            role="insurance_manager"
        )
        self.company = InsuranceCompany.objects.create(
            name="Test Insurance Company",
            ruc="1234567890123"
        )
        self.policy = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
            responsible_user=self.responsible,
        )

    def test_asset_creation_with_valid_data(self):
        asset = Asset.objects.create(
            asset_code="ASSET001",
            name="Test Laptop",
            description="A test laptop",
            brand="TestBrand",
            model="TestModel",
            serial_number="SN123456",
            asset_type="equipo_electronico",
            location="Office A",
            acquisition_date=timezone.now().date(),
            acquisition_cost=Decimal("1000.00"),
            current_value=Decimal("800.00"),
            condition_status="bueno",
            custodian=self.custodian,
            responsible_user=self.responsible,
            is_insured=True,
            insurance_policy=self.policy
        )
        self.assertEqual(asset.asset_code, "ASSET001")
        self.assertEqual(asset.name, "Test Laptop")
        self.assertEqual(asset.asset_type, "equipo_electronico")
        self.assertTrue(asset.is_insured)
        self.assertEqual(asset.insurance_policy, self.policy)

    def test_asset_unique_asset_code(self):
        Asset.objects.create(
            asset_code="UNIQUE001",
            name="Test Asset",
            asset_type="equipo_electronico",
            location="Test Location",
            acquisition_date=timezone.now().date(),
            acquisition_cost=Decimal("1000.00"),
            current_value=Decimal("1000.00"),
            custodian=self.custodian,
            responsible_user=self.responsible,
        )
        with self.assertRaises(Exception):  # IntegrityError
            Asset.objects.create(
                asset_code="UNIQUE001",  # Duplicate
                name="Another Asset",
                asset_type="equipo_electronico",
                location="Test Location",
                acquisition_date=timezone.now().date(),
                acquisition_cost=Decimal("1000.00"),
                current_value=Decimal("1000.00"),
                custodian=self.custodian,
                responsible_user=self.responsible,
            )

    def test_asset_validation_negative_values(self):
        asset = Asset(
            asset_code="TEST001",
            name="Test Asset",
            asset_type="equipo_electronico",
            location="Test Location",
            acquisition_date=timezone.now().date(),
            acquisition_cost=Decimal("-100.00"),  # Negative
            current_value=Decimal("1000.00"),
            custodian=self.custodian,
            responsible_user=self.responsible,
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_asset_str_method(self):
        asset = Asset.objects.create(
            asset_code="STR001",
            name="Test Asset",
            asset_type="equipo_electronico",
            location="Test Location",
            acquisition_date=timezone.now().date(),
            acquisition_cost=Decimal("1000.00"),
            current_value=Decimal("1000.00"),
            custodian=self.custodian,
            responsible_user=self.responsible,
        )
        expected_str = "STR001 - Test Asset"
        self.assertEqual(str(asset), expected_str)
