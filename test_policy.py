# Test script to identify the exact validation error
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seguros.settings')
django.setup()

from decimal import Decimal
from datetime import date, timedelta
from policies.models import Policy
from companies.models import InsuranceCompany
from accounts.models import UserProfile

# Get or create test data
try:
    company = InsuranceCompany.objects.first()
    user = UserProfile.objects.filter(role='admin').first()
    
    if not company or not user:
        print("❌ Necesitas ejecutar primero la creación de usuarios y compañías")
        exit(1)
    
    today = date.today()
    
    # Try to create a policy
    print("Intentando crear póliza...")
    policy = Policy.objects.create(
        policy_number='TEST-001',
        insurance_company=company,
        group_type='patrimoniales',
        subgroup='Daños',
        branch='Incendio',
        start_date=today,
        end_date=today + timedelta(days=365),
        objeto_asegurado='Test',
        prima=Decimal('5000.00'),
        costo_servicio=Decimal('100.00'),
        insured_value=Decimal('500000.00'),
        modalidad_facturacion='anual',
        status='active',
        responsible_user=user
    )
    
    print(f"✅ Póliza creada: {policy.policy_number}")
    policy.delete()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
