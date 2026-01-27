# Test fixtures and setup utilities
import os
from datetime import date, timedelta
from decimal import Decimal

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "seguros.settings")
django.setup()

from accounts.models import UserProfile
from companies.models import InsuranceCompany


def create_test_users():
    """Create test users if they don't exist"""
    users_data = [
        {
            "username": "admin_test",
            "password": "testpass123",
            "role": "admin",
            "first_name": "Admin",
            "last_name": "Test",
        },
        {
            "username": "manager_test",
            "password": "testpass123",
            "role": "insurance_manager",
            "first_name": "Manager",
            "last_name": "Test",
        },
        {
            "username": "requester_test",
            "password": "testpass123",
            "role": "requester",
            "first_name": "Requester",
            "last_name": "Test",
        },
    ]

    created_users = []
    for user_data in users_data:
        user, created = UserProfile.objects.get_or_create(
            username=user_data["username"], defaults=user_data
        )
        if created:
            print(f"✅ Usuario creado: {user.username} ({user.role})")
        else:
            print(f"⚠️  Usuario ya existe: {user.username}")
        created_users.append(user)

    return created_users


def create_test_companies():
    """Create test insurance companies if they don't exist"""
    companies_data = [
        {
            "name": "Compañía de Seguros Test S.A.",
            "ruc": "1234567890123",
            "address": "Calle Test 123",
            "phone": "+593987654321",
            "email": "contacto@testcompany.com",
        },
        {
            "name": "Aseguradora Nacional Test",
            "ruc": "9876543210987",
            "address": "Av. Principal 456",
            "phone": "+593987654322",
            "email": "info@nacionaltest.com",
        },
    ]

    created_companies = []
    for company_data in companies_data:
        company, created = InsuranceCompany.objects.get_or_create(
            ruc=company_data["ruc"], defaults=company_data
        )
        if created:
            print(f"✅ Compañía creada: {company.name}")
        else:
            print(f"⚠️  Compañía ya existe: {company.name}")
        created_companies.append(company)

    return created_companies


def setup_test_data():
    """Setup all test data"""
    print("🚀 Configurando datos de prueba...")

    users = create_test_users()
    companies = create_test_companies()

    print(f"✅ Setup completado: {len(users)} usuarios, {len(companies)} compañías")
    return users, companies


if __name__ == "__main__":
    setup_test_data()
    setup_test_data()
