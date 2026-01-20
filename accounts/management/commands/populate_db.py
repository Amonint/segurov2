"""
WORKING Django Management Command to populate database with complete test data.
All fields properly configured to match model requirements.
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
    help = 'Populate database with complete test data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Poblando base de datos completa...'))

        try:
            with transaction.atomic():
                # Users
                self.stdout.write('Creando usuarios...')
                users = self.create_users()
                self.stdout.write(self.style.SUCCESS(f'✓ {len(users)} usuarios creados'))

                # Companies
                self.stdout.write('Creando compañías de seguros...')
                companies = self.create_companies()
                self.stdout.write(self.style.SUCCESS(f'✓ {len(companies)} compañías creadas'))

                # Brokers
                self.stdout.write('Creando corredores...')
                brokers = self.create_brokers()
                self.stdout.write(self.style.SUCCESS(f'✓ {len(brokers)} corredores creados'))

                # Policies
                self.stdout.write('Creando pólizas...')
                policies = self.create_policies(companies, brokers, users)
                self.stdout.write(self.style.SUCCESS(f'✓ {len(policies)} pólizas creadas'))

                # Assets
                self.stdout.write('Creando bienes...')
                assets = self.create_assets(policies, users)
                self.stdout.write(self.style.SUCCESS(f'✓ {len(assets)} bienes creados'))

                # Claims
                self.stdout.write('Creando siniestros...')
                claims = self.create_claims(assets, users)
                self.stdout.write(self.style.SUCCESS(f'✓ {len(claims)} siniestros creados'))

                # Invoices
                self.stdout.write('Creando facturas...')
                invoices = self.create_invoices(policies)
                self.stdout.write(self.style.SUCCESS(f'✓ {len(invoices)} facturas creadas'))

            self.stdout.write(self.style.SUCCESS('\n' + '='*70))
            self.stdout.write(self.style.SUCCESS('✅ ¡Base de datos poblada exitosamente!'))
            self.stdout.write(self.style.SUCCESS('='*70))
            self.print_credentials()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))

    def create_users(self):
        """Create test users with proper roles"""
        users = []

        # Admin
        try:
            admin = UserProfile.objects.get(username='admin')
        except UserProfile.DoesNotExist:
            admin = UserProfile.objects.create_superuser(
                username='admin',
                email='admin@utpl.edu.ec',
                password='admin123',
                first_name='Admin',
                last_name='Sistema'
            )
        admin.role = 'admin'
        admin.department = 'Administración'
        admin.save()
        users.append(admin)

        # Managers
        for name in [('Maria', 'Lopez'), ('Juan', 'Perez')]:
            username = f'{name[0].lower()}.{name[1].lower()}'
            try:
                user = UserProfile.objects.get(username=username)
            except UserProfile.DoesNotExist:
                user = UserProfile.objects.create_user(
                    username=username,
                    email=f'{username}@utpl.edu.ec',
                    password='manager123',
                    first_name=name[0],
                    last_name=name[1]
                )
            user.role = 'insurance_manager'
            user.department = 'Seguros'
            user.save()
            users.append(user)

        # Custodians
        for i, name in enumerate([('Ana', 'Garcia'), ('Pedro', 'Martinez'), ('Lucia', 'Rodriguez')]):
            username = f'{name[0].lower()}.{name[1].lower()}'
            try:
                user = UserProfile.objects.get(username=username)
            except UserProfile.DoesNotExist:
                user = UserProfile.objects.create_user(
                    username=username,
                    email=f'{username}@utpl.edu.ec',
                    password='custodian123',
                    first_name=name[0],
                    last_name=name[1]
                )
            user.role = 'requester'
            user.department = ['Sistemas', 'Infraestructura', 'Laboratorios'][i]
            user.save()
            users.append(user)

        return users

    def create_companies(self):
        """Create insurance companies"""
        companies = []
        for name in ['Seguros Equinoccial', 'Seguros Sucre', 'Latina Seguros']:
            company, _ = InsuranceCompany.objects.get_or_create(
                name=name,
                defaults={
                    'ruc': f'179{random.randint(1000000, 9999999)}001',
                    'address': 'Quito, Ecuador',
                    'phone': '+593 2 298 3800',
                    'email': f'info@{name.lower().replace(" ", "")}.com'
                }
            )
            companies.append(company)
        return companies

    def create_brokers(self):
        """Create insurance brokers"""
        brokers = []
        for name in ['Corredores Asociados', 'Broker Ecuador']:
            broker, _ = Broker.objects.get_or_create(
                name=name,
                defaults={
                    'ruc': f'179{random.randint(1000000, 9999999)}001',
                    'address': 'Quito, Ecuador',
                    'phone': '+593 2 245 6789',
                    'email': f'info@{name.lower().replace(" ", "")}.com',
                    'commission_percentage': Decimal('5.00')
                }
            )
            brokers.append(broker)
        return brokers

    def create_policies(self, companies, brokers, users):
        """Create insurance policies with all required fields"""
        policies = []
        managers = [u for u in users if u.role == 'insurance_manager']
        admin = users[0]

        for i in range(5):
            today = date.today()
            
            # Create policy with all required fields
            policy = Policy.objects.create(
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
            policies.append(policy)
        
        return policies

    def create_assets(self, policies, users):
        """Create assets assigned to custodians"""
        assets = []
        custodians = [u for u in users if u.role == 'requester']
        
        asset_types = ['Computadora', 'Laptop', 'Proyector', 'Impresora', 'Servidor']
        brands = ['Dell', 'HP', 'Lenovo', 'Epson', 'Canon']
        
        for i in range(15):
            asset = Asset.objects.create(
                asset_code=f'ASSET-{str(i+1).zfill(5)}',
                asset_type=random.choice(asset_types),
                description=f'Equipo de oficina {i+1}',
                brand=random.choice(brands),
                model='Standard',
                serial_number=f'SN{random.randint(100000, 999999)}',
                purchase_date=date.today() - timedelta(days=365),
                purchase_value=Decimal('2000.00'),
                current_value=Decimal('1500.00'),
                location='Oficina Central',
                custodian=random.choice(custodians) if custodians else users[0],
                is_insured=True,
                insurance_policy=random.choice(policies),
                status='active'
            )
            assets.append(asset)
        
        return assets

    def create_claims(self, assets, users):
        """Create claims for damaged assets"""
        claims = []
        managers = [u for u in users if u.role in ['admin', 'insurance_manager']]
        
        statuses = ['reported', 'documentation_pending', 'sent_to_insurer', 'under_evaluation']
        
        for i in range(10):
            asset = random.choice(assets)
            claim = Claim.objects.create(
                claim_number=f'CLM-2026-{str(i+1).zfill(6)}',
                policy=asset.insurance_policy,
                asset_code=asset.asset_code,
                asset_type=asset.asset_type,
                asset_description=asset.description,
                incident_date=date.today() - timedelta(days=random.randint(10, 60)),
                incident_location=asset.location,
                incident_description=f'Daño reportado en {asset.asset_type}',
                estimated_loss=Decimal(str(random.randint(500, 2000))),
                status=random.choice(statuses),
                reported_by=asset.custodian,
                assigned_to=random.choice(managers) if managers else users[0]
            )
            claims.append(claim)
        
        return claims

    def create_invoices(self, policies):
        """Create invoices for policies"""
        invoices = []
        
        for i, policy in enumerate(policies[:3]):
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
        
        return invoices

    def print_credentials(self):
        """Print login credentials"""
        self.stdout.write(self.style.SUCCESS('\n📋 CREDENCIALES DE ACCESO'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.WARNING('\n👤 ADMINISTRADOR:'))
        self.stdout.write('   Usuario: admin')
        self.stdout.write('   Contraseña: admin123')
        self.stdout.write(self.style.WARNING('\n👥 GERENTES DE SEGUROS:'))
        self.stdout.write('   Usuarios: maria.lopez / juan.perez')
        self.stdout.write('   Contraseña: manager123')
        self.stdout.write(self.style.WARNING('\n🔑 CUSTODIOS:'))
        self.stdout.write('   Usuarios: ana.garcia / pedro.martinez / lucia.rodriguez')
        self.stdout.write('   Contraseña: custodian123')
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🌐 Accede al sistema en: http://127.0.0.1:8000'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
