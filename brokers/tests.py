from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from brokers.models import Broker


class BrokerModelTests(TestCase):
    def test_broker_creation_with_valid_data(self):
        broker = Broker.objects.create(
            name="Test Broker",
            ruc="1234567890123",
            address="Test Address",
            phone="+593987654321",
            email="contact@testbroker.com",
            contact_person="Jane Doe",
            commission_percentage=Decimal("5.00")
        )
        self.assertEqual(broker.name, "Test Broker")
        self.assertEqual(broker.ruc, "1234567890123")
        self.assertEqual(broker.commission_percentage, Decimal("5.00"))
        self.assertTrue(broker.is_active)

    def test_broker_unique_constraints(self):
        Broker.objects.create(
            name="Unique Broker",
            ruc="1234567890123",
            commission_percentage=Decimal("5.00")
        )
        with self.assertRaises(Exception):  # IntegrityError
            Broker.objects.create(
                name="Unique Broker",  # Duplicate name
                ruc="9876543210987",
                commission_percentage=Decimal("5.00")
            )
        with self.assertRaises(Exception):  # IntegrityError
            Broker.objects.create(
                name="Another Broker",
                ruc="1234567890123",  # Duplicate RUC
                commission_percentage=Decimal("5.00")
            )

    def test_broker_validation_invalid_ruc_length(self):
        broker = Broker(
            name="Test Broker",
            ruc="123456789",  # Too short
            commission_percentage=Decimal("5.00")
        )
        with self.assertRaises(ValidationError):
            broker.full_clean()

    def test_broker_validation_invalid_commission_percentage(self):
        broker = Broker(
            name="Test Broker",
            ruc="1234567890123",
            commission_percentage=Decimal("150.00")  # Over 100%
        )
        with self.assertRaises(ValidationError):
            broker.full_clean()

    def test_broker_validation_negative_commission_percentage(self):
        broker = Broker(
            name="Test Broker",
            ruc="1234567890123",
            commission_percentage=Decimal("-5.00")  # Negative
        )
        with self.assertRaises(ValidationError):
            broker.full_clean()

    def test_broker_str_method(self):
        broker = Broker.objects.create(
            name="Test Broker",
            ruc="1234567890123",
            commission_percentage=Decimal("10.50")
        )
        expected_str = "Test Broker (10.50%)"
        self.assertEqual(str(broker), expected_str)
