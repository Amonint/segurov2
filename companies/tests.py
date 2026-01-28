from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from companies.models import EmissionRights, InsuranceCompany


class InsuranceCompanyModelTests(TestCase):
    def test_company_creation_with_valid_data(self):
        company = InsuranceCompany.objects.create(
            name="Test Insurance Company",
            ruc="1234567890123",
            address="Test Address",
            phone="+593987654321",
            email="contact@testcompany.com",
            contact_person="John Doe"
        )
        self.assertEqual(company.name, "Test Insurance Company")
        self.assertEqual(company.ruc, "1234567890123")
        self.assertTrue(company.is_active)
        self.assertEqual(str(company), "Test Insurance Company")

    def test_company_unique_constraints(self):
        InsuranceCompany.objects.create(
            name="Test Company",
            ruc="1234567890123"
        )
        with self.assertRaises(Exception):  # IntegrityError
            InsuranceCompany.objects.create(
                name="Test Company",  # Duplicate name
                ruc="9876543210987"
            )
        with self.assertRaises(Exception):  # IntegrityError
            InsuranceCompany.objects.create(
                name="Another Company",
                ruc="1234567890123"  # Duplicate RUC
            )

    def test_company_str_method(self):
        company = InsuranceCompany.objects.create(
            name="Test Company",
            ruc="1234567890123"
        )
        self.assertEqual(str(company), "Test Company")


class EmissionRightsModelTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username="testuser",
            password="testpass123",
            role="admin"
        )

    def test_emission_rights_creation(self):
        rights = EmissionRights.objects.create(
            min_amount=Decimal("0.00"),
            max_amount=Decimal("1000.00"),
            emission_right=Decimal("10.00"),
            valid_from=timezone.now().date(),
            created_by=self.user
        )
        self.assertEqual(rights.min_amount, Decimal("0.00"))
        self.assertEqual(rights.max_amount, Decimal("1000.00"))
        self.assertEqual(rights.emission_right, Decimal("10.00"))
        self.assertTrue(rights.is_active)

    def test_get_emission_right_in_range(self):
        EmissionRights.objects.create(
            min_amount=Decimal("0.00"),
            max_amount=Decimal("1000.00"),
            emission_right=Decimal("10.00"),
            valid_from=timezone.now().date(),
            created_by=self.user
        )
        manager = EmissionRights.objects
        result = manager.get_emission_right(Decimal("500.00"))
        self.assertEqual(result, Decimal("10.00"))

    def test_get_emission_right_out_of_range(self):
        EmissionRights.objects.create(
            min_amount=Decimal("0.00"),
            max_amount=Decimal("1000.00"),
            emission_right=Decimal("10.00"),
            valid_from=timezone.now().date(),
            created_by=self.user
        )
        manager = EmissionRights.objects
        result = manager.get_emission_right(Decimal("1500.00"))
        self.assertEqual(result, Decimal("0.00"))

    def test_get_emission_right_no_active_rights(self):
        manager = EmissionRights.objects
        result = manager.get_emission_right(Decimal("500.00"))
        self.assertEqual(result, Decimal("0.00"))
