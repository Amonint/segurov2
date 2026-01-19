"""
Django Management Command to populate the database with realistic test data.

Usage:
    python manage.py populate_db

This will create:
- Users (admin, managers, custodians) with passwords
- Insurance companies and brokers
- Policies with different statuses
- Assets assigned to custodians
- Claims with various statuses
- Invoices (paid and pending)
- Settlements

All data is calculated dynamically in the backend.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta, date
from decimal import Decimal
import random

from accounts.models import UserProfile
from companies.models import InsuranceCompany
from brokers.models import Broker
from policies.models import Policy
from assets.models import Asset
from claims.models import Claim, ClaimSettlement
from invoices.models import Invoice


class Command(BaseCommand):
    help = 'Populate database with realistic test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting database population...'))

        with transaction.atomic():
            # Create data in order of dependencies
            self.stdout.write('Creating users...')
            users = self.create_users()
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))

            self.stdout.write('Creating insurance companies...')
            companies = self.create_insurance_companies()
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(companies)} insurance companies'))

            self.stdout.write('Creating brokers...')
            brokers = self.create_brokers()
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(brokers)} brokers'))

            self.stdout.write('Creating policies...')
            policies = self.create_policies(companies, brokers, users)
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(policies)} policies'))

            self.stdout.write('Creating assets...')
            assets = self.create_assets(policies, users)
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(assets)} assets'))

            self.stdout.write('Creating claims...')
            claims = self.create_claims(assets, policies, users)
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(claims)} claims'))

            self.stdout.write('Creating invoices...')
            invoices = self.create_invoices(policies, users)
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(invoices)} invoices'))

            # settlements = self.create_settlements(claims, users)
            # self.stdout.write(self.style.SUCCESS(f'✓ Created {len(settlements)} settlements'))
            self.stdout.write(self.style.WARNING('⚠ Settlements creation skipped (can be added manually)'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.print_credentials(users)

    def clear_data(self):
        """Clear existing data"""
        ClaimSettlement.objects.all().delete()
        Claim.objects.all().delete()
        Invoice.objects.all().delete()
        Asset.objects.all().delete()
        Policy.objects.all().delete()
        Broker.objects.all().delete()
        InsuranceCompany.objects.all().delete()
        UserProfile.objects.filter(is_superuser=False).delete()

    def create_users(self):
        """Create users with different roles"""
        users = []

        # Admin user
        try:
            admin = UserProfile.objects.get(username='admin')
            admin.email = 'admin@seguros.utpl.edu.ec'
            admin.role = 'admin'
            admin.first_name = 'Carlos'
            admin.last_name = 'Administrador'
            admin.department = 'Administración'
            admin.phone = '+593 99 123 4567'
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password('admin123')
            admin.save()
        except UserProfile.DoesNotExist:
            admin = UserProfile.objects.create_user(
                username='admin',
                email='admin@seguros.utpl.edu.ec',
                password='admin123',
                first_name='Carlos',
                last_name='Administrador',
                role='admin',
                department='Administración',
                phone='+593 99 123 4567',
                is_staff=True,
                is_superuser=True
            )
        users.append(admin)

        # Insurance Managers
        managers_data = [
            ('maria.lopez', 'María', 'López', 'Gestión de Seguros', '+593 99 234 5678'),
            ('juan.perez', 'Juan', 'Pérez', 'Gestión de Seguros', '+593 99 345 6789'),
        ]
        for username, first_name, last_name, dept, phone in managers_data:
            try:
                user = UserProfile.objects.get(username=username)
                user.email = f'{username}@seguros.utpl.edu.ec'
                user.role = 'insurance_manager'
                user.first_name = first_name
                user.last_name = last_name
                user.department = dept
                user.phone = phone
                user.set_password('manager123')
                user.save()
            except UserProfile.DoesNotExist:
                user = UserProfile.objects.create_user(
                    username=username,
                    email=f'{username}@seguros.utpl.edu.ec',
                    password='manager123',
                    first_name=first_name,
                    last_name=last_name,
                    role='insurance_manager',
                    department=dept,
                    phone=phone
                )
            users.append(user)

        # Custodians (Requesters)
        custodians_data = [
            ('ana.garcia', 'Ana', 'García', 'Sistemas', '+593 99 456 7890'),
            ('pedro.martinez', 'Pedro', 'Martínez', 'Infraestructura', '+593 99 567 8901'),
            ('lucia.rodriguez', 'Lucía', 'Rodríguez', 'Laboratorios', '+593 99 678 9012'),
            ('diego.sanchez', 'Diego', 'Sánchez', 'Biblioteca', '+593 99 789 0123'),
            ('carmen.torres', 'Carmen', 'Torres', 'Administración', '+593 99 890 1234'),
        ]
        for username, first_name, last_name, dept, phone in custodians_data:
            try:
                user = UserProfile.objects.get(username=username)
                user.email = f'{username}@seguros.utpl.edu.ec'
                user.role = 'requester'
                user.first_name = first_name
                user.last_name = last_name
                user.department = dept
                user.phone = phone
                user.set_password('custodian123')
                user.save()
            except UserProfile.DoesNotExist:
                user = UserProfile.objects.create_user(
                    username=username,
                    email=f'{username}@seguros.utpl.edu.ec',
                    password='custodian123',
                    first_name=first_name,
                    last_name=last_name,
                    role='requester',
                    department=dept,
                    phone=phone
                )
            users.append(user)

        return users

    def create_insurance_companies(self):
        """Create insurance companies"""
        companies_data = [
            {
                'name': 'Seguros Equinoccial',
                'ruc': '1790011674001',
                'address': 'Av. 12 de Octubre N24-562 y Cordero, Quito',
                'phone': '+593 2 298 3800',
                'email': 'info@equinoccial.com',
                'contact_person': 'Roberto Andrade',
            },
            {
                'name': 'Seguros Sucre',
                'ruc': '1790338860001',
                'address': 'Av. Amazonas N39-123 y Arízaga, Quito',
                'phone': '+593 2 244 9370',
                'email': 'contacto@segurossucre.com',
                'contact_person': 'Patricia Morales',
            },
            {
                'name': 'Latina Seguros',
                'ruc': '1790406049001',
                'address': 'Av. República E7-153 y Almagro, Quito',
                'phone': '+593 2 333 0800',
                'email': 'servicio@latinaseguros.com',
                'contact_person': 'Fernando Vega',
            },
            {
                'name': 'Seguros Colonial',
                'ruc': '1790011682001',
                'address': 'Av. Naciones Unidas E2-30 y Shyris, Quito',
                'phone': '+593 2 298 0200',
                'email': 'info@colonial.com.ec',
                'contact_person': 'Mónica Herrera',
            },
        ]

        companies = []
        for data in companies_data:
            company = InsuranceCompany.objects.create(**data)
            companies.append(company)

        return companies

    def create_brokers(self):
        """Create insurance brokers"""
        brokers_data = [
            {
                'name': 'Corredores Asociados S.A.',
                'ruc': '1792345678001',
                'address': 'Av. 6 de Diciembre N34-451, Quito',
                'phone': '+593 2 245 6789',
                'email': 'info@corredoresasociados.com',
                'contact_person': 'Alberto Ruiz',
            },
            {
                'name': 'Broker Seguros del Ecuador',
                'ruc': '1793456789001',
                'address': 'Av. República del Salvador N34-127, Quito',
                'phone': '+593 2 246 7890',
                'email': 'contacto@brokerecuador.com',
                'contact_person': 'Sandra Jiménez',
            },
        ]

        brokers = []
        for data in brokers_data:
            broker = Broker.objects.create(**data)
            brokers.append(broker)

        return brokers

    def create_policies(self, companies, brokers, users):
        """Create insurance policies"""
        policies = []
        admin = users[0]
        managers = [u for u in users if u.role == 'insurance_manager']

        # Policy templates
        policy_templates = [
            {
                'group_type': 'patrimoniales',
                'branch': 'Incendio y Líneas Aliadas',
                'insured_value': Decimal('500000.00'),
                'premium': Decimal('5000.00'),
                'deductible': Decimal('1000.00'),
            },
            {
                'group_type': 'patrimoniales',
                'branch': 'Robo y Asalto',
                'insured_value': Decimal('300000.00'),
                'premium': Decimal('3500.00'),
                'deductible': Decimal('500.00'),
            },
            {
                'group_type': 'patrimoniales',
                'branch': 'Equipo Electrónico',
                'insured_value': Decimal('200000.00'),
                'premium': Decimal('2500.00'),
                'deductible': Decimal('300.00'),
            },
            {
                'group_type': 'responsabilidad',
                'branch': 'Responsabilidad Civil General',
                'insured_value': Decimal('1000000.00'),
                'premium': Decimal('8000.00'),
                'deductible': Decimal('2000.00'),
            },
            {
                'group_type': 'personas',
                'branch': 'Accidentes Personales',
                'insured_value': Decimal('100000.00'),
                'premium': Decimal('1500.00'),
                'deductible': Decimal('0.00'),
            },
        ]

        statuses = ['active', 'active', 'active', 'pending', 'expired']
        
        for i, template in enumerate(policy_templates):
            company = random.choice(companies)
            broker = random.choice(brokers) if random.random() > 0.3 else None
            responsible = random.choice(managers)
            status = statuses[i % len(statuses)]

            # Calculate dates based on status
            if status == 'active':
                start_date = date.today() - timedelta(days=random.randint(30, 180))
                end_date = start_date + timedelta(days=365)
            elif status == 'pending':
                start_date = date.today() + timedelta(days=random.randint(10, 30))
                end_date = start_date + timedelta(days=365)
            else:  # expired
                end_date = date.today() - timedelta(days=random.randint(10, 60))
                start_date = end_date - timedelta(days=365)

            issue_date = start_date - timedelta(days=random.randint(5, 15))

            policy = Policy.objects.create(
                policy_number=f'POL-{date.today().year}-{str(i+1).zfill(6)}',
                insurance_company=company,
                broker=broker,
                group_type=template['group_type'],
                branch=template['branch'],
                start_date=start_date,
                end_date=end_date,
                issue_date=issue_date,
                insured_value=template['insured_value'],
                premium=template['premium'],
                deductible=template['deductible'],
                payment_frequency='annual',
                status=status,
                responsible_user=responsible,
                coverage_description=f'Cobertura completa para {template["branch"]}',
                created_by=admin
            )
            policies.append(policy)

        return policies

    def create_assets(self, policies, users):
        """Create assets assigned to custodians"""
        assets = []
        custodians = [u for u in users if u.role == 'requester']
        active_policies = [p for p in policies if p.status == 'active']

        asset_templates = [
            {'type': 'Computadora', 'brand': 'Dell', 'model': 'OptiPlex 7090'},
            {'type': 'Laptop', 'brand': 'HP', 'model': 'EliteBook 840 G8'},
            {'type': 'Proyector', 'brand': 'Epson', 'model': 'PowerLite L610U'},
            {'type': 'Impresora', 'brand': 'Canon', 'model': 'imageRUNNER ADVANCE'},
            {'type': 'Servidor', 'brand': 'Dell', 'model': 'PowerEdge R750'},
            {'type': 'Switch', 'brand': 'Cisco', 'model': 'Catalyst 9300'},
            {'type': 'Escritorio', 'brand': 'Muebles Modernos', 'model': 'Ejecutivo Premium'},
            {'type': 'Silla', 'brand': 'Ergonómica Pro', 'model': 'Executive Plus'},
            {'type': 'Aire Acondicionado', 'brand': 'LG', 'model': 'Dual Inverter'},
            {'type': 'Microscopio', 'brand': 'Olympus', 'model': 'CX43'},
        ]

        for i in range(25):  # Create 25 assets
            template = random.choice(asset_templates)
            custodian = random.choice(custodians)
            policy = random.choice(active_policies)
            
            purchase_date = date.today() - timedelta(days=random.randint(365, 1825))
            value = Decimal(str(random.randint(500, 5000)))

            asset = Asset.objects.create(
                asset_code=f'ASSET-{str(i+1).zfill(5)}',
                asset_type=template['type'],
                description=f'{template["brand"]} {template["model"]}',
                brand=template['brand'],
                model=template['model'],
                serial_number=f'SN{random.randint(100000, 999999)}',
                purchase_date=purchase_date,
                purchase_value=value,
                current_value=value * Decimal('0.7'),  # Depreciation
                location=custodian.department,
                custodian=custodian,
                is_insured=True,
                insurance_policy=policy,
                status='active'
            )
            assets.append(asset)

        return assets

    def create_claims(self, assets, policies, users):
        """Create claims with various statuses"""
        claims = []
        custodians = [u for u in users if u.role == 'requester']
        managers = [u for u in users if u.role in ['admin', 'insurance_manager']]

        statuses = [
            'reported', 'documentation_pending', 'sent_to_insurer',
            'under_evaluation', 'liquidated', 'paid', 'closed'
        ]

        # Create 15 claims
        for i in range(15):
            asset = random.choice(assets)
            custodian = asset.custodian
            policy = asset.insurance_policy
            assigned_to = random.choice(managers)
            status = random.choice(statuses)

            incident_date = date.today() - timedelta(days=random.randint(10, 180))
            estimated_loss = asset.current_value * Decimal(str(random.uniform(0.1, 0.8)))

            claim = Claim.objects.create(
                claim_number=f'CLM-{date.today().year}-{str(i+1).zfill(6)}',
                policy=policy,
                asset_code=asset.asset_code,
                asset_type=asset.asset_type,
                asset_description=asset.description,
                incident_date=incident_date,
                incident_location=asset.location,
                incident_description=self.generate_incident_description(asset.asset_type),
                estimated_loss=estimated_loss,
                status=status,
                reported_by=custodian,
                assigned_to=assigned_to
            )
            claims.append(claim)

        return claims

    def create_invoices(self, policies, users):
        """Create invoices for policies"""
        invoices = []
        admin = users[0]

        for i, policy in enumerate(policies):
            if policy.status in ['active', 'expired']:
                # Create invoice
                invoice_date = policy.start_date
                due_date = invoice_date + timedelta(days=30)
                
                base_amount = policy.premium
                tax_amount = base_amount * Decimal('0.12')  # 12% IVA
                total_amount = base_amount + tax_amount

                # Determine payment status
                if policy.status == 'expired' or random.random() > 0.3:
                    payment_status = 'paid'
                    payment_date = due_date - timedelta(days=random.randint(1, 20))
                else:
                    payment_status = 'pending'
                    payment_date = None

                invoice = Invoice.objects.create(
                    invoice_number=f'INV-{date.today().year}-{str(i+1).zfill(6)}',
                    policy=policy,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    base_amount=base_amount,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    payment_status=payment_status,
                    payment_date=payment_date,
                    created_by=admin
                )
                invoices.append(invoice)

        return invoices

    def create_settlements(self, claims, users):
        """Create settlements for liquidated/paid claims"""
        settlements = []
        admin = users[0]

        liquidated_claims = [c for c in claims if c.status in ['liquidated', 'paid', 'closed']]

        for i, claim in enumerate(liquidated_claims):
            total_claim = claim.estimated_loss
            deductible = claim.policy.deductible if claim.policy else Decimal('500.00')
            depreciation = total_claim * Decimal('0.1')
            final_payment = total_claim - deductible - depreciation

            status = 'paid' if claim.status == 'paid' else 'approved'

            settlement = ClaimSettlement.objects.create(
                claim=claim,
                settlement_number=f'SET-{date.today().year}-{str(i+1).zfill(6)}',
                settlement_date=claim.created_at.date() + timedelta(days=random.randint(30, 90)),
                total_claim_amount=total_claim,
                deductible_amount=deductible,
                depreciation_amount=depreciation,
                final_payment_amount=final_payment,
                status=status,
                created_by=admin
            )
            settlements.append(settlement)

        return settlements

    def generate_incident_description(self, asset_type):
        """Generate realistic incident descriptions"""
        descriptions = {
            'Computadora': 'Daño por sobretensión eléctrica que afectó la placa madre',
            'Laptop': 'Caída accidental que causó daño en la pantalla y teclado',
            'Proyector': 'Falla en el sistema de enfriamiento, sobrecalentamiento',
            'Impresora': 'Daño por derrame de líquido en componentes internos',
            'Servidor': 'Falla en disco duro, pérdida parcial de datos',
            'Switch': 'Daño por descarga eléctrica durante tormenta',
            'Escritorio': 'Daño estructural por impacto durante mudanza',
            'Silla': 'Rotura del mecanismo de ajuste de altura',
            'Aire Acondicionado': 'Falla en compresor, requiere reemplazo',
            'Microscopio': 'Daño en lentes por manipulación inadecuada',
        }
        return descriptions.get(asset_type, 'Daño reportado en el equipo')

    def print_credentials(self, users):
        """Print user credentials"""
        self.stdout.write(self.style.SUCCESS('\n📋 CREDENCIALES DE USUARIOS'))
        self.stdout.write(self.style.SUCCESS('='*50))
        
        self.stdout.write(self.style.WARNING('\n👤 ADMINISTRADOR:'))
        self.stdout.write(f'   Usuario: admin')
        self.stdout.write(f'   Contraseña: admin123')
        
        self.stdout.write(self.style.WARNING('\n👥 GERENTES DE SEGUROS:'))
        self.stdout.write(f'   Usuario: maria.lopez / juan.perez')
        self.stdout.write(f'   Contraseña: manager123')
        
        self.stdout.write(self.style.WARNING('\n🔑 CUSTODIOS (Requesters):'))
        self.stdout.write(f'   Usuarios: ana.garcia, pedro.martinez, lucia.rodriguez,')
        self.stdout.write(f'             diego.sanchez, carmen.torres')
        self.stdout.write(f'   Contraseña: custodian123')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
