from policies.models import Policy
from accounts.models import UserProfile
from companies.models import InsuranceCompany
from brokers.models import Broker
import traceback

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
        from decimal import Decimal
        from datetime import date, timedelta
        
        print("Intentando crear póliza simple...")
        p = Policy(
            policy_number='TEST-DIAG-002',
            insurance_company=company,
            broker=broker,
            group_type='patrimoniales',
            subgroup='Daños',
            branch='Incendio',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            objeto_asegurado='Test',
            prima=Decimal('100.00'),
            costo_servicio=Decimal('10.00'),
            insured_value=Decimal('1000.00'),
            status='active',
            responsible_user=admin
        )
        p.save()
        print(f"Póliza creada: {p.pk}")
        
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
