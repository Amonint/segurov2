import traceback

from accounts.models import UserProfile
from brokers.models import Broker
from companies.models import InsuranceCompany
from policies.models import Policy

print("Diagnosticando...")
try:
    admin = UserProfile.objects.filter(role="admin").first()
    company = InsuranceCompany.objects.first()
    broker = Broker.objects.first()

    if not all([admin, company, broker]):
        print("Faltan dependencias")
    else:
        print(f"Admin: {admin}, Company: {company}")

        # Try creating ONE policy explicitly
        from datetime import date, timedelta
        from decimal import Decimal

        print("Intentando crear póliza simple...")
        p = Policy(
            policy_number="TEST-DIAG-002",
            insurance_company=company,
            broker=broker,
            group_type="patrimoniales",
            subgroup="Daños",
            branch="Incendio",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            objeto_asegurado="Test",
            prima=Decimal("100.00"),
            costo_servicio=Decimal("10.00"),
            insured_value=Decimal("1000.00"),
            status="active",
            responsible_user=admin,
        )
        p.save()
        print(f"Póliza creada: {p.pk}")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
