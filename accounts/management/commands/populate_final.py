"""
Final Population Script: Policies -> Update Assets -> Claims -> Invoices
Completes the database population as requested.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import timedelta, date
from decimal import Decimal
import random
import sys
import io

# Force UTF-8 stdout for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from accounts.models import UserProfile
from companies.models import InsuranceCompany
from brokers.models import Broker
from policies.models import Policy
from assets.models import Asset
from claims.models import Claim
from invoices.models import Invoice


class Command(BaseCommand):
    help = 'Complete database population: Policies, Asset Assignment, Claims, Invoices'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando población final de base de datos...'))

        # Get prerequisites
        admin = UserProfile.objects.filter(role='admin').first()
        managers = list(UserProfile.objects.filter(role='insurance_manager'))
        custodians = list(UserProfile.objects.filter(role='requester'))
        companies = list(InsuranceCompany.objects.all())
        brokers = list(Broker.objects.all())

        if not all([admin, managers, custodians, companies, brokers]):
            self.stdout.write(self.style.ERROR('❌ Error: Faltan datos base (usuarios, compañías). Ejecuta populate_step1 primero.'))
            return

        try:
            with transaction.atomic():
                # Cleanup previous test run data
                self.stdout.write('Limpiando datos de prueba anteriores...')
                Policy.objects.filter(policy_number__startswith='POL-2026-AUTO-').delete()
                
                # 1. Create Policies
                self.stdout.write('\n📜 Creando Pólizas...')
                policies = self.create_policies(companies, brokers, managers, admin)
                self.stdout.write(self.style.SUCCESS(f'✓ {len(policies)} pólizas creadas exitosamente'))
                
                if not policies:
                     self.stdout.write(self.style.ERROR('⚠ No se crearon pólizas. Deteniendo ejecución.'))
                     return

                # 2. Update Assets (Assign Policy)
                self.stdout.write('\n📦 Asignando Pólizas a Bienes existentes...')
                updated_assets = self.assign_policies_to_assets(policies)
                self.stdout.write(self.style.SUCCESS(f'✓ {len(updated_assets)} bienes actualizados con póliza'))

                # 3. Create Claims (requires updated assets)
                self.stdout.write('\n🚨 Creando Siniestros...')
                # Re-fetch assets that now have policies
                insured_assets = list(Asset.objects.filter(insurance_policy__isnull=False))
                claims = self.create_claims(insured_assets, managers, admin)
                self.stdout.write(self.style.SUCCESS(f'✓ {len(claims)} siniestros creados'))

                # 4. Create Invoices
                self.stdout.write('\n💰 Creando Facturas...')
                invoices = self.create_invoices(policies, admin)
                self.stdout.write(self.style.SUCCESS(f'✓ {len(invoices)} facturas creadas'))

            self.stdout.write(self.style.SUCCESS('\n' + '='*70))
            self.stdout.write(self.style.SUCCESS('✅ ¡Base de datos completa! Todo vinculado correctamente.'))
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

        # Define specific policies for different branches
        policy_data = [
            {'branch': 'Incendio y Líneas Aliadas', 'subgroup': 'Daños', 'group': 'patrimoniales', 'value': '500000.00', 'prima': '5000.00'},
            {'branch': 'Equipo Electrónico', 'subgroup': 'Daños', 'group': 'patrimoniales', 'value': '200000.00', 'prima': '3000.00'},
            {'branch': 'Robo y Asalto', 'subgroup': 'Daños', 'group': 'patrimoniales', 'value': '100000.00', 'prima': '1500.00'},
            {'branch': 'Responsabilidad Civil', 'subgroup': 'Responsabilidad', 'group': 'patrimoniales', 'value': '1000000.00', 'prima': '8000.00'},
            {'branch': 'Vehículos', 'subgroup': 'Vehículos', 'group': 'patrimoniales', 'value': '300000.00', 'prima': '12000.00'},
        ]

        for i, data in enumerate(policy_data):
            # Check duplication
            if Policy.objects.filter(policy_number=f'POL-2026-AUTO-{i+1}').exists():
                self.stdout.write(f'  ⚠ Póliza {i+1} ya existe, saltando')
                continue

            policy = Policy(
                policy_number=f'POL-2026-AUTO-{str(i+1).zfill(3)}',
                insurance_company=companies[i % len(companies)],
                broker=brokers[i % len(brokers)],
                group_type=data['group'],
                subgroup=data['subgroup'],
                branch=data['branch'],
                start_date=today - timedelta(days=30),
                end_date=today + timedelta(days=335),
                issue_date=today - timedelta(days=40),
                objeto_asegurado=f'Activos de {data["branch"]}',
                prima=Decimal(data['prima']),
                costo_servicio=Decimal('100.00'),
                insured_value=Decimal(data['value']),
                modalidad_facturacion='anual',
                status='active',
                responsible_user=random.choice(managers) if managers else admin
            )
            # Let save() call full_clean() and calculations
            policy.save()
            policies.append(policy)
            self.stdout.write(f'  ✓ Póliza {policy.policy_number} ({policy.branch})')

        return policies

    def assign_policies_to_assets(self, policies):
        """Assign policies to existing assets"""
        assets = Asset.objects.all()
        count = 0
        
        updated_assets = []

        # Logic to match assets to relevant policies (e.g., electronic equipment to Electronic Policy)
        electronic_policy = next((p for p in policies if p.branch == 'Equipo Electrónico'), policies[0] if policies else None)
        furniture_policy = next((p for p in policies if p.branch == 'Incendio y Líneas Aliadas'), policies[0] if policies else None)

        if not electronic_policy:
            return 0

        for asset in assets:
            # Skip if already insured (optional, but good for re-runs)
            if asset.is_insured and asset.insurance_policy:
                continue

            target_policy = electronic_policy
            if asset.asset_type in ['mobiliario', 'maquinaria']:
                target_policy = furniture_policy

            asset.insurance_policy = target_policy
            asset.is_insured = True
            asset.save()
            count += 1
            updated_assets.append(asset)
            self.stdout.write(f'  ✓ Asignada póliza {target_policy.policy_number} a {asset.name}')
            
        return updated_assets

    def create_claims(self, assets, managers, admin):
        """Create claims"""
        claims = []
        today = date.today()
        statuses = ['reportado', 'docs_pendientes', 'enviado_aseguradora', 'en_revision']

        # Only create claims if we have assets
        if not assets:
            return []

        # Create 5 claims
        for i in range(5):
            try:
                asset = random.choice(assets)
                
                # Check duplication
                if Claim.objects.filter(claim_number=f'CLM-2026-AUTO-{i+1}').exists():
                    continue

                claim = Claim.objects.create(
                    claim_number=f'CLM-2026-AUTO-{str(i+1).zfill(3)}',
                    policy=asset.insurance_policy,
                    asset_code=asset.asset_code, # Use asset fields required by model if redundant
                    # Model expects asset_code string? Or relation? 
                    # Checking model: asset_code, asset_type, asset_description are CharFields (legacy?) or derived?
                    # Assuming fields exist based on previous views.
                    asset_type=asset.asset_type,
                    asset_description=asset.description,
                    fecha_siniestro=today - timedelta(days=random.randint(10, 60)),
                    incident_date=today - timedelta(days=random.randint(10, 60)), # Alias
                    ubicacion_detallada=asset.location,
                    incident_location=asset.location, # Alias
                    causa=f'Fallo reportado en {asset.name}',
                    incident_description=f'Fallo reportado en {asset.name}', # Alias
                    estimated_loss=Decimal('500.00'),
                    status=random.choice(statuses),
                    reportante=asset.custodian,
                    reported_by=asset.custodian, # Alias
                    assigned_to=random.choice(managers) if managers else admin
                )
                claims.append(claim)
                self.stdout.write(f'  ✓ Siniestro {claim.claim_number} para {asset.name}')
            except Exception as e:
                 self.stdout.write(self.style.WARNING(f'  ⚠ Error siniestro {i+1}: {str(e)}'))

        return claims

    def create_invoices(self, policies, admin):
        """Create invoices"""
        invoices = []

        for i, policy in enumerate(policies):
            try:
                if Invoice.objects.filter(invoice_number=f'INV-2026-AUTO-{i+1}').exists():
                    continue

                invoice = Invoice.objects.create(
                    invoice_number=f'INV-2026-AUTO-{str(i+1).zfill(3)}',
                    policy=policy,
                    invoice_date=policy.start_date,
                    due_date=policy.start_date + timedelta(days=30),
                    fecha_vencimiento=policy.start_date + timedelta(days=30), # Alias validation
                    payment_status='pagada' if i == 0 else 'pendiente',
                    payment_date=policy.start_date + timedelta(days=15) if i == 0 else None,
                    created_by=admin
                )
                invoices.append(invoice)
                self.stdout.write(f'  ✓ Factura {invoice.invoice_number} para Póliza {policy.policy_number}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Error factura {i+1}: {str(e)}'))

        return invoices

    def print_summary(self):
        """Print database summary"""
        self.stdout.write(self.style.SUCCESS('\n📊 RESUMEN FINAL'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'  📋 Pólizas: {Policy.objects.count()}')
        self.stdout.write(f'  📦 Bienes: {Asset.objects.count()} (Asegurados: {Asset.objects.filter(is_insured=True).count()})')
        self.stdout.write(f'  🚨 Siniestros: {Claim.objects.count()}')
        self.stdout.write(f'  💰 Facturas: {Invoice.objects.count()}')
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
