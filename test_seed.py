"""
Test script to debug Policy creation
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "seguros.settings")

import django

django.setup()

import traceback
from datetime import date, timedelta
from decimal import Decimal

from accounts.models import UserProfile
from brokers.models import Broker
from companies.models import InsuranceCompany
from policies.models import Policy

print("=== Debugging Policy Creation ===")

# Get required dependencies
admin = UserProfile.objects.filter(role="admin").first()
company = InsuranceCompany.objects.first()
broker = Broker.objects.first()

print(f"Admin: {admin}")
print(f"Company: {company}")
print(f"Broker: {broker}")

if not all([admin, company, broker]):
    print("Missing dependencies! Creating them first...")

    if not admin:
        admin = UserProfile.objects.create_user(
            username="admin_test",
            password="Admin123!",
            email="admin_test@test.com",
            role="admin",
        )
        print(f"Created admin: {admin}")

    if not company:
        company = InsuranceCompany.objects.create(
            name="Test Company",
            ruc="1234567890001",
            address="Test Address",
            city="Quito",
            phone="022123456",
            email="test@company.com",
            is_active=True,
        )
        print(f"Created company: {company}")

    if not broker:
        broker = Broker.objects.create(
            name="Test Broker",
            ruc="0987654321001",
            license_number="TEST-001",
            address="Test Address",
            city="Quito",
            phone="022654321",
            email="test@broker.com",
            commission_rate=Decimal("10.00"),
            is_active=True,
        )
        print(f"Created broker: {broker}")

# Now try to create a policy
print("\n=== Creating Policy ===")
try:
    from django.db import models

    p = Policy(
        insurance_company=company,
        broker=broker,
        group_type="patrimoniales",
        subgroup="Test Subgroup",
        branch="Test Branch",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        objeto_asegurado="Test object",
        prima=Decimal("1000.00"),
        costo_servicio=Decimal("0.00"),
        insured_value=Decimal("100000.00"),
        status="active",
        responsible_user=admin,
    )

    # Generate policy number
    p.policy_number = Policy.generate_policy_number()

    # Set fiscal values manually
    p.contrib_superintendencia = p.prima * Decimal("0.035")
    p.contrib_seguro_campesino = p.prima * Decimal("0.005")
    p.derecho_emision = Decimal("5.00")
    p.base_imponible = (
        p.prima
        + p.contrib_superintendencia
        + p.contrib_seguro_campesino
        + p.derecho_emision
    )
    p.iva = p.base_imponible * Decimal("0.15")
    p.total_facturado = p.base_imponible + p.iva

    # Save using base model save
    models.Model.save(p)

    print(f"SUCCESS! Policy created: {p.policy_number}")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
