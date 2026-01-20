import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seguros.settings')
django.setup()

from policies.models import Policy
from accounts.models import UserProfile
from companies.models import InsuranceCompany
from brokers.models import Broker
import traceback
from decimal import Decimal
from datetime import date, timedelta

print("Diagnosticando...")
try:
    admin = UserProfile.objects.filter(role='admin').first()
    company = InsuranceCompany.objects.first()
    broker = Broker.objects.first()
    
    if not all([admin, company, broker]):
        print("Faltan dependencias")
    else:
        print(f"Admin: {admin}, Company: {company}")
        
        # Try creating ONE policy explicitly
        print("Intentando crear póliza simple...")
        p = Policy(
            policy_number='TEST-DIAG-003',
            insurance_company=company,
            broker=broker,
            group_type='patrimoniales',
            subgroup='Daños',
            branch='Incendio',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            objeto_asegurado='Test',
            prima=Decimal('5000.00'), # Valor que causaba error: 5000 * 0.035 = 175.0 (un decimal, ok). 
            # Probemos uno que de 3 decimales: 100.55 * 0.035 = 3.51925
            costo_servicio=Decimal('10.00'),
            insured_value=Decimal('1000.00'),
            status='active',
            responsible_user=admin
        )
        p.save()
        print(f"✅ Póliza creada exitosamente: {p.policy_number}")
        print(f"  - Prima: {p.prima}")
        print(f"  - Contrib. Super: {p.contrib_superintendencia}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    traceback.print_exc()
