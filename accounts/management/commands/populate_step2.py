"""
Complete database population - Step 2: Policies, Assets, Claims, Invoices
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import timedelta, date
from decimal import Decimal
import random

from accounts.models import UserProfile
from companies.models import InsuranceCompany
from brokers.models import Broker
from policies.models import Policy
from assets.models import Asset
from claims.models import Claim
from invoices.models import Invoice


class Command(BaseCommand):
    help = 'Populate database - Step 2: Policies, Assets, Claims, Invoices'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Poblando pólizas, bienes, siniestros y facturas...'))

        # Get existing data
        admin = UserProfile.objects.filter(role='admin').first()
        managers = list(UserProfile.objects.filter(role='insurance_manager'))
        custodians = list(UserProfile.objects.filter(role='requester'))
        companies = list(InsuranceCompany.objects.all())
        brokers = list(Broker.objects.all())

        if not all([admin, managers, custodians, companies, brokers]):
            self.stdout.write(self.style.ERROR('❌ Error: Ejecuta primero "python manage.py populate_step1"'))
            return

        try:
            # Create Policies
            self.stdout.write('Creando pólizas...')
            policies = self.create_policies(companies, brokers, managers, admin)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(policies)} pólizas creadas'))

            if not policies:
                self.stdout.write(self.style.WARNING('⚠ No se pudieron crear pólizas. Creando datos sin pólizas...'))
                return

            # Create Assets
            self.stdout.write('Creando bienes...')
            assets = self.create_assets(policies, custodians)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(assets)} bienes creados'))

            # Create Claims
            self.stdout.write('Creando siniestros...')
            claims = self.create_claims(assets, managers, admin)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(claims)} siniestros creados'))

            # Create Invoices
            self.stdout.write('Creando facturas...')
            invoices = self.create_invoices(policies)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(invoices)} facturas creadas'))

            self.stdout.write(self.style.SUCCESS('\n' + '='*70))
            self.stdout.write(self.style.SUCCESS('✅ ¡Base de datos completamente poblada!'))
            self.stdout.write(self.style.SUCCESS('='*70))
            self.print_summary()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))

    def create_policies(self, companies, brokers, managers, admin):
        """Create policies"""
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
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Error en póliza {i+1}: {str(e)}'))
                continue

        return policies

    def create_assets(self, policies, custodians):
        """Create assets"""
        assets = []
        today = date.today()
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
                    insurance_policy=random.choice(policies),
                    status='active'
                )
                assets.append(asset)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Error en bien {i+1}: {str(e)}'))
                continue

        return assets

    def create_claims(self, assets, managers, admin):
        """Create claims"""
        claims = []
        today = date.today()
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
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Error en siniestro {i+1}: {str(e)}'))
                continue

        return claims

    def create_invoices(self, policies):
        """Create invoices"""
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
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Error en factura {i+1}: {str(e)}'))
                continue

        return invoices

    def print_summary(self):
        """Print database summary"""
        self.stdout.write(self.style.SUCCESS('\n📊 RESUMEN DE LA BASE DE DATOS'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'  👤 Usuarios: {UserProfile.objects.count()}')
        self.stdout.write(f'  🏢 Compañías: {InsuranceCompany.objects.count()}')
        self.stdout.write(f'  🤝 Corredores: {Broker.objects.count()}')
        self.stdout.write(f'  📋 Pólizas: {Policy.objects.count()}')
        self.stdout.write(f'  📦 Bienes: {Asset.objects.count()}')
        self.stdout.write(f'  🚨 Siniestros: {Claim.objects.count()}')
        self.stdout.write(f'  💰 Facturas: {Invoice.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n🌐 Accede al sistema: http://127.0.0.1:8000'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
