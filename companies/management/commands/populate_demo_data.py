from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from accounts.models import UserProfile
from companies.models import InsuranceCompany
from brokers.models import Broker
from assets.models import Asset
from policies.models import Policy
from claims.models import Claim
from invoices.models import Invoice

class Command(BaseCommand):
    help = 'Populates the database with demo data (Assets, Policies, Claims, Invoices)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting data population...")

        try:
            with transaction.atomic():
                # 1. Get or Create Key Users
                admin_user = UserProfile.objects.filter(is_superuser=True).first()
                if not admin_user:
                    self.stdout.write(self.style.ERROR("No admin user found! Please create one first."))
                    return

                client_user = UserProfile.objects.filter(username='cliente1').first()
                if not client_user:
                    client_user = UserProfile.objects.create_user(username='cliente1', email='cliente@demo.com', password='password123', role='requester', first_name='Maria', last_name='Gomez')
                    self.stdout.write("Created user: cliente1")
                
                adjuster_user = UserProfile.objects.filter(username='ajustador1').first()
                if not adjuster_user:
                     adjuster_user = UserProfile.objects.create_user(username='ajustador1', email='adjuster@demo.com', password='password123', role='insurance_manager', first_name='Juan', last_name='Perez')
                     self.stdout.write("Created user: ajustador1")

                # 2. Companies
                company1, _ = InsuranceCompany.objects.get_or_create(
                    name='Seguros Confianza',
                    defaults={'ruc': '1790000000001', 'address': 'Av. Amazonas', 'phone': '022222222', 'email': 'contact@confianza.com', 'contact_person': 'Contact 1', 'is_active': True}
                )
                company2, _ = InsuranceCompany.objects.get_or_create(
                    name='Aseguradora del Sur',
                    defaults={'ruc': '1790000000002', 'address': 'Calle Larga', 'phone': '042222222', 'email': 'info@delsur.com', 'contact_person': 'Contact 2', 'is_active': True}
                )

                # 3. Policies
                # Policy 1: Vehicle
                policy_vh, _ = Policy.objects.get_or_create(
                    policy_number='POL-VH-2025-001',
                    defaults={
                        'insurance_company': company1,
                        'group_type': 'patrimoniales', # Fixed choice
                        'subgroup': 'Livianos', 'branch': 'Automotores',
                        'start_date': '2025-01-01', 'end_date': '2025-12-31', 'issue_date': '2025-01-01',
                        'status': 'active', 'insured_value': Decimal('45000.00'),
                        'prima': Decimal('1200.00'),
                        'coverage_description': 'Cobertura completa', 'objeto_asegurado': 'Toyota Fortuner 2024',
                        'responsible_user': admin_user
                    }
                )

                # Policy 2: Property
                policy_pr, _ = Policy.objects.get_or_create(
                    policy_number='POL-PR-2025-002',
                    defaults={
                        'insurance_company': company2,
                        'group_type': 'patrimoniales', # Fixed choice
                        'subgroup': 'Incendio', 'branch': 'Incendio y Lineas Aliadas',
                        'start_date': '2025-03-01', 'end_date': '2026-02-28', 'issue_date': '2025-03-01',
                        'status': 'active', 'insured_value': Decimal('120000.00'),
                        'prima': Decimal('2500.00'),
                        'coverage_description': 'Todo riesgo', 'objeto_asegurado': 'Departamento Centro',
                        'responsible_user': admin_user
                    }
                )
                self.stdout.write("Policies check complete.")

                # 4. Assets
                asset_veh, _ = Asset.objects.get_or_create(
                    asset_code='VEH-001',
                    defaults={
                        'name': 'Toyota Fortuner 2024', 
                        'asset_type': 'vehiculo', # Fixed choice
                        'description': 'SUV 4x4 Negro', 'location': 'Quito',
                        'acquisition_cost': Decimal('50000.00'), 'current_value': Decimal('45000.00'), 
                        'acquisition_date': '2024-01-15',
                        'condition_status': 'bueno', # Fixed choice
                        'is_insured': True,
                        'custodian': client_user, 'responsible_user': client_user,
                        'insurance_policy': policy_vh,
                        'brand': 'Toyota', 'model': 'Fortuner', 'serial_number': 'SN-001'
                    }
                )

                asset_prop, _ = Asset.objects.get_or_create(
                    asset_code='PROP-001',
                    defaults={
                        'name': 'Departamento Centro', 
                        'asset_type': 'otros', # Fixed choice (Propiedad is not in choices)
                        'description': 'Departamento 3 dormitorios', 'location': 'Guayaquil',
                        'acquisition_cost': Decimal('110000.00'), 'current_value': Decimal('120000.00'), 
                        'acquisition_date': '2022-05-20',
                        'condition_status': 'bueno', # Fixed choice
                        'is_insured': True,
                        'custodian': client_user, 'responsible_user': client_user,
                        'insurance_policy': policy_pr
                    }
                )
                self.stdout.write("Assets check complete.")

                # 5. Claims
                claim1, created1 = Claim.objects.get_or_create(
                    claim_number='CLM-2025-001',
                    defaults={
                        'policy': policy_vh, 'asset': asset_veh,
                        'reportante_id': client_user.id, 'reported_by': client_user,
                        'fecha_siniestro': '2025-06-15', 'incident_date': '2025-06-15',
                        'incident_description': 'Choque lateral leve', 'causa': 'Colisión',
                        'ubicacion_detallada': 'Av. Shyris', 'incident_location': 'Av. Shyris',
                        'status': 'pendiente', 'estimated_loss': Decimal('1500.00'),
                        'asset_type': 'vehiculo', # Fixed choice (must match asset.asset_type usually, or just string)
                        'asset_description': 'Toyota Fortuner', 'asset_code': 'VEH-001'
                    }
                )

                claim2, created2 = Claim.objects.get_or_create(
                    claim_number='CLM-2025-002',
                    defaults={
                        'policy': policy_pr, 'asset': asset_prop,
                        'reportante_id': client_user.id, 'reported_by': client_user,
                        'fecha_siniestro': '2025-07-20', 'incident_date': '2025-07-20',
                        'incident_description': 'Rotura tubería', 'causa': 'Daño por agua',
                        'ubicacion_detallada': 'Edif Torre', 'incident_location': 'Edif Torre',
                        'status': 'en_revision', 'estimated_loss': Decimal('850.00'),
                        'asset_type': 'otros', # Fixed choice
                        'asset_description': 'Departamento', 'asset_code': 'PROP-001'
                    }
                )
                self.stdout.write("Claims check complete.")
                
                # 6. Invoices
                inv1, _ = Invoice.objects.get_or_create(
                    invoice_number='FAC-001',
                    defaults={
                        'policy': policy_vh, 
                        'invoice_date': '2025-01-01', 'due_date': '2025-01-15',
                        'total_amount': Decimal('1500.00'), 'premium': Decimal('1200.00'), 
                        'superintendence_contribution': Decimal('42.00'), 'farm_insurance_contribution': Decimal('6.00'), 
                        'emission_rights': Decimal('0.00'), 'tax_base': Decimal('1248.00'), 'iva': Decimal('187.20'),
                        'payment_status': 'paid', 'created_by': admin_user
                    }
                )
                
                self.stdout.write(self.style.SUCCESS("Successfully populated demo data!"))

        except Exception as e:
            import traceback
            self.stdout.write(self.style.ERROR(f"Error populating data: {str(e)}"))
            self.stdout.write(traceback.format_exc())
            raise e
