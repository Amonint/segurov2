# Script para crear pólizas, bienes, siniestros y facturas
# Ejecutar con: python manage.py shell < create_remaining_data.py

from decimal import Decimal
from datetime import date, timedelta
import random

from accounts.models import UserProfile
from companies.models import InsuranceCompany
from brokers.models import Broker
from policies.models import Policy
from assets.models import Asset
from claims.models import Claim
from invoices.models import Invoice

print("🚀 Creando datos restantes...")

# Get existing data
admin = UserProfile.objects.filter(role='admin').first()
managers = list(UserProfile.objects.filter(role='insurance_manager'))
custodians = list(UserProfile.objects.filter(role='requester'))
companies = list(InsuranceCompany.objects.all())
brokers = list(Broker.objects.all())

if not all([admin, managers, custodians, companies, brokers]):
    print("❌ Error: Ejecuta primero 'python manage.py populate_step1'")
    exit(1)

# Create Policies
print("\nCreando pólizas...")
policies = []
today = date.today()

for i in range(5):
    try:
        policy = Policy(
            policy_number=f'POL-2026-{str(i+1).zfill(6)}',
            insurance_company=random.choice(companies),
            broker=random.choice(brokers) if i % 2 == 0 else None,
            group_type='patrimoniales',
            subgroup='Daños',
            branch='Incendio y Líneas Aliadas',
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=335),
            issue_date=today - timedelta(days=40),
            objeto_asegurado='Bienes de la institución',
            prima=Decimal('5000.00'),
            costo_servicio=Decimal('100.00'),
            insured_value=Decimal('500000.00'),
            modalidad_facturacion='anual',
            status='active',
            responsible_user=random.choice(managers) if managers else admin
        )
        policy.save()
        policies.append(policy)
        print(f"  ✓ Póliza {policy.policy_number} creada")
    except Exception as e:
        print(f"  ❌ Error creando póliza {i+1}: {e}")

print(f"✓ {len(policies)} pólizas creadas")

# Create Assets
print("\nCreando bienes...")
assets = []
asset_types = ['Computadora', 'Laptop', 'Proyector', 'Impresora', 'Servidor']
brands = ['Dell', 'HP', 'Lenovo', 'Epson', 'Canon']

for i in range(15):
    try:
        asset = Asset.objects.create(
            asset_code=f'ASSET-{str(i+1).zfill(5)}',
            asset_type=random.choice(asset_types),
            description=f'Equipo de oficina {i+1}',
            brand=random.choice(brands),
            model='Standard',
            serial_number=f'SN{random.randint(100000, 999999)}',
            purchase_date=today - timedelta(days=365),
            purchase_value=Decimal('2000.00'),
            current_value=Decimal('1500.00'),
            location='Oficina Central',
            custodian=random.choice(custodians),
            is_insured=True,
            insurance_policy=random.choice(policies) if policies else None,
            status='active'
        )
        assets.append(asset)
        print(f"  ✓ Bien {asset.asset_code} creado")
    except Exception as e:
        print(f"  ❌ Error creando bien {i+1}: {e}")

print(f"✓ {len(assets)} bienes creados")

# Create Claims
print("\nCreando siniestros...")
claims = []
statuses = ['reported', 'documentation_pending', 'sent_to_insurer', 'under_evaluation']

for i in range(10):
    if not assets:
        break
    try:
        asset = random.choice(assets)
        claim = Claim.objects.create(
            claim_number=f'CLM-2026-{str(i+1).zfill(6)}',
            policy=asset.insurance_policy,
            asset_code=asset.asset_code,
            asset_type=asset.asset_type,
            asset_description=asset.description,
            incident_date=today - timedelta(days=random.randint(10, 60)),
            incident_location=asset.location,
            incident_description=f'Daño reportado en {asset.asset_type}',
            estimated_loss=Decimal(str(random.randint(500, 2000))),
            status=random.choice(statuses),
            reported_by=asset.custodian,
            assigned_to=random.choice(managers) if managers else admin
        )
        claims.append(claim)
        print(f"  ✓ Siniestro {claim.claim_number} creado")
    except Exception as e:
        print(f"  ❌ Error creando siniestro {i+1}: {e}")

print(f"✓ {len(claims)} siniestros creados")

# Create Invoices
print("\nCreando facturas...")
invoices = []

for i, policy in enumerate(policies[:3]):
    try:
        invoice = Invoice.objects.create(
            invoice_number=f'INV-2026-{str(i+1).zfill(6)}',
            policy=policy,
            invoice_date=policy.start_date,
            due_date=policy.start_date + timedelta(days=30),
            base_amount=policy.prima,
            tax_amount=policy.prima * Decimal('0.12'),
            total_amount=policy.prima * Decimal('1.12'),
            payment_status='paid' if i == 0 else 'pending',
            payment_date=policy.start_date + timedelta(days=15) if i == 0 else None
        )
        invoices.append(invoice)
        print(f"  ✓ Factura {invoice.invoice_number} creada")
    except Exception as e:
        print(f"  ❌ Error creando factura {i+1}: {e}")

print(f"✓ {len(invoices)} facturas creadas")

print("\n" + "="*70)
print("✅ Base de datos poblada completamente!")
print("="*70)
print(f"\n📊 Resumen:")
print(f"  - Usuarios: {UserProfile.objects.count()}")
print(f"  - Compañías: {InsuranceCompany.objects.count()}")
print(f"  - Corredores: {Broker.objects.count()}")
print(f"  - Pólizas: {Policy.objects.count()}")
print(f"  - Bienes: {Asset.objects.count()}")
print(f"  - Siniestros: {Claim.objects.count()}")
print(f"  - Facturas: {Invoice.objects.count()}")
print("\n🌐 Accede al sistema en: http://127.0.0.1:8000")
print("="*70)
