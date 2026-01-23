"""
Management command to seed the database with sample data
Creates users, companies, policies, assets, and claims with realistic data
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed database with sample data for testing and demonstration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING("[*] Iniciando poblacion de base de datos...")
        )

        with transaction.atomic():
            if options["clear"]:
                self.clear_data()

            # Create data in order of dependencies
            users = self.create_users()
            companies = self.create_insurance_companies()
            brokers = self.create_brokers()
            policies = self.create_policies(companies, brokers, users)
            assets = self.create_assets(policies, users)
            claims = self.create_claims(assets, policies, users)

            self.stdout.write(
                self.style.SUCCESS("\n[OK] Base de datos poblada exitosamente!")
            )
            self.print_summary(users, companies, brokers, policies, assets, claims)

    def clear_data(self):
        """Clear existing data"""
        from accounts.models import UserProfile
        from assets.models import Asset
        from brokers.models import Broker
        from claims.models import Claim, ClaimDocument, ClaimTimeline
        from companies.models import InsuranceCompany
        from policies.models import Coverage, Policy, PolicyDocument

        self.stdout.write("[*] Limpiando datos existentes...")

        ClaimTimeline.objects.all().delete()
        ClaimDocument.objects.all().delete()
        Claim.objects.all().delete()
        Asset.objects.all().delete()
        Coverage.objects.all().delete()
        PolicyDocument.objects.all().delete()
        Policy.objects.all().delete()
        Broker.objects.all().delete()
        InsuranceCompany.objects.all().delete()
        UserProfile.objects.exclude(is_superuser=True).delete()

    def create_users(self):
        """Create sample users with different roles"""
        from accounts.models import UserProfile

        self.stdout.write("[*] Creando usuarios...")

        users_data = [
            # Administradores
            {
                "username": "admin",
                "email": "admin@utpl.edu.ec",
                "password": "Admin123!",
                "full_name": "Administrador del Sistema",
                "role": "admin",
                "department": "TI",
                "phone": "0991234567",
                "is_superuser": True,
                "is_staff": True,
            },
            {
                "username": "carlos.admin",
                "email": "carlos.admin@utpl.edu.ec",
                "password": "Admin123!",
                "full_name": "Carlos Rodríguez Mendoza",
                "role": "admin",
                "department": "Administración",
                "phone": "0992345678",
                "is_staff": True,
            },
            # Gerentes de Seguros
            {
                "username": "maria.gerente",
                "email": "maria.gerente@utpl.edu.ec",
                "password": "Gerente123!",
                "full_name": "María García López",
                "role": "insurance_manager",
                "department": "Seguros",
                "phone": "0993456789",
            },
            {
                "username": "juan.gerente",
                "email": "juan.gerente@utpl.edu.ec",
                "password": "Gerente123!",
                "full_name": "Juan Pérez Sánchez",
                "role": "insurance_manager",
                "department": "Seguros",
                "phone": "0994567890",
            },
            # Custodios de Bienes
            {
                "username": "ana.custodio",
                "email": "ana.custodio@utpl.edu.ec",
                "password": "Custodio123!",
                "full_name": "Ana García Martínez",
                "role": "requester",
                "department": "Facultad de Ingeniería",
                "phone": "0995678901",
            },
            {
                "username": "luis.custodio",
                "email": "luis.custodio@utpl.edu.ec",
                "password": "Custodio123!",
                "full_name": "Luis Torres Ramírez",
                "role": "requester",
                "department": "Facultad de Ciencias",
                "phone": "0996789012",
            },
            {
                "username": "sofia.custodio",
                "email": "sofia.custodio@utpl.edu.ec",
                "password": "Custodio123!",
                "full_name": "Sofía Mendoza Vargas",
                "role": "requester",
                "department": "Biblioteca Central",
                "phone": "0997890123",
            },
            {
                "username": "pedro.custodio",
                "email": "pedro.custodio@utpl.edu.ec",
                "password": "Custodio123!",
                "full_name": "Pedro Sánchez Rivera",
                "role": "requester",
                "department": "Laboratorio de Computación",
                "phone": "0998901234",
            },
        ]

        created_users = []
        for user_data in users_data:
            password = user_data.pop("password")

            # Check if user exists first
            existing_user = UserProfile.objects.filter(
                username=user_data["username"]
            ).first()
            if existing_user:
                self.stdout.write(f"   [-] Usuario existente: {existing_user.username}")
                created_users.append(existing_user)
                continue

            # Create new user with password
            is_superuser = user_data.pop("is_superuser", False)
            is_staff = user_data.pop("is_staff", False)

            user = UserProfile.objects.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=password,
            )
            # Set additional fields
            user.full_name = user_data.get("full_name", "")
            user.role = user_data.get("role", "requester")
            user.department = user_data.get("department", "")
            user.phone = user_data.get("phone", "")
            user.is_superuser = is_superuser
            user.is_staff = is_staff
            user.save()

            self.stdout.write(
                f"   [+] Usuario creado: {user.username} ({user.get_role_display()})"
            )
            created_users.append(user)

        return created_users

    def create_insurance_companies(self):
        """Create sample insurance companies"""
        from companies.models import InsuranceCompany

        self.stdout.write("[*] Creando companias de seguros...")

        companies_data = [
            {
                "name": "Seguros Equinoccial S.A.",
                "ruc": "1790012345001",
                "address": "Av. Republica del Salvador N34-127, Quito",
                "phone": "022456789",
                "email": "contacto@equinoccial.com.ec",
                "contact_person": "Roberto Gomez",
                "is_active": True,
            },
            {
                "name": "ACE Seguros S.A.",
                "ruc": "1791234567001",
                "address": "Av. Amazonas N23-45, Quito",
                "phone": "022567890",
                "email": "info@ace.com.ec",
                "contact_person": "Carolina Mendez",
                "is_active": True,
            },
            {
                "name": "Seguros del Pichincha S.A.",
                "ruc": "1792345678001",
                "address": "Av. Naciones Unidas E5-67, Quito",
                "phone": "022678901",
                "email": "clientes@segurosdelpichincha.com",
                "contact_person": "Fernando Luna",
                "is_active": True,
            },
        ]

        created_companies = []
        for company_data in companies_data:
            company, created = InsuranceCompany.objects.get_or_create(
                ruc=company_data["ruc"], defaults=company_data
            )
            if created:
                self.stdout.write(f"   [+] Compania creada: {company.name}")
            else:
                self.stdout.write(f"   [-] Compania existente: {company.name}")
            created_companies.append(company)

        return created_companies

    def create_brokers(self):
        """Create sample insurance brokers"""
        from brokers.models import Broker

        self.stdout.write("[*] Creando corredores de seguros...")

        brokers_data = [
            {
                "name": "Tecniseguros S.A.",
                "ruc": "1793456789001",
                "address": "Av. 6 de Diciembre N32-45, Quito",
                "phone": "022789012",
                "email": "info@tecniseguros.com.ec",
                "contact_person": "Patricia Vera",
                "commission_percentage": Decimal("10.00"),
                "is_active": True,
            },
            {
                "name": "Asertec Brokers",
                "ruc": "1794567890001",
                "address": "Av. Eloy Alfaro N34-56, Quito",
                "phone": "022890123",
                "email": "contacto@asertec.com.ec",
                "contact_person": "Miguel Herrera",
                "commission_percentage": Decimal("12.00"),
                "is_active": True,
            },
        ]

        created_brokers = []
        for broker_data in brokers_data:
            broker, created = Broker.objects.get_or_create(
                ruc=broker_data["ruc"], defaults=broker_data
            )
            if created:
                self.stdout.write(f"   [+] Corredor creado: {broker.name}")
            else:
                self.stdout.write(f"   [-] Corredor existente: {broker.name}")
            created_brokers.append(broker)

        return created_brokers

    def create_policies(self, companies, brokers, users):
        """Create sample insurance policies"""
        from policies.models import Coverage, Policy

        self.stdout.write("[*] Creando polizas de seguro...")

        admin_user = next((u for u in users if u.role == "admin"), users[0])

        today = timezone.now().date()

        policies_data = [
            {
                "group_type": "patrimoniales",
                "subgroup": "Vehiculos",
                "branch": "Todo Riesgo Vehicular",
                "objeto_asegurado": "Flota vehicular institucional UTPL",
                "insurance_company": companies[0],
                "broker": brokers[0],
                "start_date": today - timedelta(days=180),
                "end_date": today + timedelta(days=185),
                "insured_value": Decimal("500000.00"),
                "prima": Decimal("5000.00"),
                "status": "active",
                "coverage_description": "Poliza de vehiculos institucionales UTPL",
                "responsible_user": admin_user,
                "coverages": [
                    {
                        "nombre": "Danos propios",
                        "valor_asegurado": Decimal("100000.00"),
                        "porcentaje_deducible": Decimal("5.00"),
                    },
                    {
                        "nombre": "Responsabilidad civil",
                        "valor_asegurado": Decimal("200000.00"),
                        "deducible": Decimal("500.00"),
                    },
                    {
                        "nombre": "Robo total",
                        "valor_asegurado": Decimal("100000.00"),
                        "porcentaje_deducible": Decimal("10.00"),
                    },
                ],
            },
            {
                "group_type": "patrimoniales",
                "subgroup": "Equipo Electronico",
                "branch": "Todo Riesgo Electronico",
                "objeto_asegurado": "Equipos electronicos y computacionales UTPL",
                "insurance_company": companies[1],
                "broker": brokers[1],
                "start_date": today - timedelta(days=90),
                "end_date": today + timedelta(days=275),
                "insured_value": Decimal("1000000.00"),
                "prima": Decimal("8000.00"),
                "status": "active",
                "coverage_description": "Poliza de equipos electronicos y computacionales",
                "responsible_user": admin_user,
                "coverages": [
                    {
                        "nombre": "Danos por accidente",
                        "valor_asegurado": Decimal("500000.00"),
                        "porcentaje_deducible": Decimal("3.00"),
                    },
                    {
                        "nombre": "Robo",
                        "valor_asegurado": Decimal("300000.00"),
                        "deducible": Decimal("200.00"),
                    },
                    {
                        "nombre": "Fallas electricas",
                        "valor_asegurado": Decimal("200000.00"),
                        "porcentaje_deducible": Decimal("5.00"),
                    },
                ],
            },
            {
                "group_type": "patrimoniales",
                "subgroup": "Incendio",
                "branch": "Incendio y Lineas Aliadas",
                "objeto_asegurado": "Edificios e infraestructura UTPL",
                "insurance_company": companies[2],
                "broker": brokers[0],
                "start_date": today - timedelta(days=60),
                "end_date": today + timedelta(days=305),
                "insured_value": Decimal("5000000.00"),
                "prima": Decimal("25000.00"),
                "status": "active",
                "coverage_description": "Poliza contra incendio edificios UTPL",
                "responsible_user": admin_user,
                "coverages": [
                    {
                        "nombre": "Incendio",
                        "valor_asegurado": Decimal("3000000.00"),
                        "porcentaje_deducible": Decimal("2.00"),
                    },
                    {
                        "nombre": "Terremoto",
                        "valor_asegurado": Decimal("1500000.00"),
                        "porcentaje_deducible": Decimal("5.00"),
                    },
                    {
                        "nombre": "Inundacion",
                        "valor_asegurado": Decimal("500000.00"),
                        "porcentaje_deducible": Decimal("3.00"),
                    },
                ],
            },
            {
                "group_type": "patrimoniales",
                "subgroup": "Robo",
                "branch": "Robo y Asalto",
                "objeto_asegurado": "Bienes muebles UTPL",
                "insurance_company": companies[0],
                "broker": brokers[1],
                "start_date": today - timedelta(days=30),
                "end_date": today + timedelta(days=335),
                "insured_value": Decimal("200000.00"),
                "prima": Decimal("3000.00"),
                "status": "active",
                "coverage_description": "Poliza contra robo de bienes muebles",
                "responsible_user": admin_user,
                "coverages": [
                    {
                        "nombre": "Robo con violencia",
                        "valor_asegurado": Decimal("150000.00"),
                        "deducible": Decimal("1000.00"),
                    },
                    {
                        "nombre": "Hurto",
                        "valor_asegurado": Decimal("50000.00"),
                        "porcentaje_deducible": Decimal("10.00"),
                    },
                ],
            },
        ]

        created_policies = []
        for policy_data in policies_data:
            coverages_data = policy_data.pop("coverages")

            # Check if policy exists by subgroup
            existing = Policy.objects.filter(
                subgroup=policy_data["subgroup"],
                insurance_company=policy_data["insurance_company"],
            ).first()

            if existing:
                self.stdout.write(f"   -> Poliza existente: {existing.policy_number}")
                created_policies.append(existing)
                continue

            # Create policy - add missing required fields
            policy_data["costo_servicio"] = Decimal("0.00")

            policy = Policy(**policy_data)
            policy.policy_number = Policy.generate_policy_number()
            # Set fiscal values manually to avoid EmissionRights lookup
            policy.contrib_superintendencia = policy.prima * Decimal("0.035")
            policy.contrib_seguro_campesino = policy.prima * Decimal("0.005")
            policy.derecho_emision = Decimal("5.00")  # Default value
            policy.base_imponible = (
                policy.prima
                + policy.contrib_superintendencia
                + policy.contrib_seguro_campesino
                + policy.derecho_emision
            )
            policy.iva = policy.base_imponible * Decimal("0.15")
            policy.total_facturado = policy.base_imponible + policy.iva

            # Save using Django's base model save to bypass custom validation
            from django.db import models

            models.Model.save(policy)

            # Create coverages
            for cov_data in coverages_data:
                Coverage.objects.create(policy=policy, **cov_data)

            self.stdout.write(
                f"   [+] Poliza creada: {policy.policy_number} - {policy.subgroup}"
            )
            created_policies.append(policy)

        return created_policies

    def create_assets(self, policies, users):
        """Create sample assets assigned to custodians"""
        from assets.models import Asset

        self.stdout.write("[*] Creando bienes/activos...")

        # Get custodians
        custodians = [u for u in users if u.role == "requester"]
        admin_user = next((u for u in users if u.role == "admin"), users[0])

        # Get policies by type for assignment
        vehicle_policy = next(
            (p for p in policies if "Vehiculo" in p.subgroup), policies[0]
        )
        electronic_policy = next(
            (p for p in policies if "Electronico" in p.subgroup), policies[0]
        )

        today = timezone.now().date()

        assets_data = [
            # Vehículos
            {
                "name": "Toyota Hilux 2022",
                "description": "Camioneta doble cabina para uso institucional",
                "brand": "Toyota",
                "model": "Hilux SR5",
                "serial_number": "VIN-JTFHT02J920123456",
                "asset_type": "vehiculo",
                "location": "Parqueadero Principal - UTPL",
                "acquisition_date": today - timedelta(days=365),
                "acquisition_cost": Decimal("45000.00"),
                "current_value": Decimal("40500.00"),
                "condition_status": "excelente",
                "custodian": custodians[0],
                "responsible_user": admin_user,
                "is_insured": True,
                "insurance_policy": vehicle_policy,
            },
            {
                "name": "Chevrolet D-Max 2021",
                "description": "Vehículo de transporte de carga ligera",
                "brand": "Chevrolet",
                "model": "D-Max 4x4",
                "serial_number": "VIN-8LBETF1N1M0123789",
                "asset_type": "vehiculo",
                "location": "Parqueadero Secundario - Campus",
                "acquisition_date": today - timedelta(days=500),
                "acquisition_cost": Decimal("38000.00"),
                "current_value": Decimal("32300.00"),
                "condition_status": "bueno",
                "custodian": custodians[1],
                "responsible_user": admin_user,
                "is_insured": True,
                "insurance_policy": vehicle_policy,
            },
            # Equipos electrónicos
            {
                "name": "HP LaserJet Pro",
                "description": "Impresora láser multifuncional para oficina",
                "brand": "HP",
                "model": "LaserJet Pro MFP M428fdw",
                "serial_number": "CNBJ9P2345",
                "asset_type": "equipo_electronico",
                "location": "Oficina de TI - Edificio A",
                "acquisition_date": today - timedelta(days=180),
                "acquisition_cost": Decimal("850.00"),
                "current_value": Decimal("765.00"),
                "condition_status": "excelente",
                "custodian": custodians[0],
                "responsible_user": admin_user,
                "is_insured": True,
                "insurance_policy": electronic_policy,
            },
            {
                "name": "Dell OptiPlex 7090",
                "description": "Computador de escritorio para laboratorio",
                "brand": "Dell",
                "model": "OptiPlex 7090 SFF",
                "serial_number": "DELL-SVC-78901234",
                "asset_type": "equipo_electronico",
                "location": "Lab. Computación 1 - Edificio B",
                "acquisition_date": today - timedelta(days=90),
                "acquisition_cost": Decimal("1200.00"),
                "current_value": Decimal("1140.00"),
                "condition_status": "excelente",
                "custodian": custodians[2],
                "responsible_user": admin_user,
                "is_insured": True,
                "insurance_policy": electronic_policy,
            },
            {
                "name": 'MacBook Pro 14"',
                "description": "Laptop para desarrollo de software",
                "brand": "Apple",
                "model": "MacBook Pro M2 Pro",
                "serial_number": "C02XL0ABCDEF",
                "asset_type": "equipo_electronico",
                "location": "Oficina Desarrollo - Edificio C",
                "acquisition_date": today - timedelta(days=120),
                "acquisition_cost": Decimal("2500.00"),
                "current_value": Decimal("2375.00"),
                "condition_status": "excelente",
                "custodian": custodians[3],
                "responsible_user": admin_user,
                "is_insured": True,
                "insurance_policy": electronic_policy,
            },
            {
                "name": "Servidor Dell PowerEdge",
                "description": "Servidor para aplicaciones institucionales",
                "brand": "Dell",
                "model": "PowerEdge R750",
                "serial_number": "DELL-PE-R750-001",
                "asset_type": "equipo_electronico",
                "location": "Centro de Datos - Edificio TI",
                "acquisition_date": today - timedelta(days=60),
                "acquisition_cost": Decimal("15000.00"),
                "current_value": Decimal("14250.00"),
                "condition_status": "excelente",
                "custodian": custodians[0],
                "responsible_user": admin_user,
                "is_insured": True,
                "insurance_policy": electronic_policy,
            },
            # Mobiliario
            {
                "name": "Escritorio Ejecutivo",
                "description": "Escritorio de madera para oficina ejecutiva",
                "brand": "Office Depot",
                "model": "Executive 2000",
                "serial_number": "MOB-EXE-001",
                "asset_type": "mobiliario",
                "location": "Oficina Rectorado - Edificio A",
                "acquisition_date": today - timedelta(days=730),
                "acquisition_cost": Decimal("800.00"),
                "current_value": Decimal("640.00"),
                "condition_status": "bueno",
                "custodian": custodians[1],
                "responsible_user": admin_user,
                "is_insured": False,
                "insurance_policy": None,
            },
            {
                "name": "Proyector Epson",
                "description": "Proyector multimedia para aulas",
                "brand": "Epson",
                "model": "PowerLite X49",
                "serial_number": "EP-X49-2023-001",
                "asset_type": "equipo_electronico",
                "location": "Aula Magna - Edificio Central",
                "acquisition_date": today - timedelta(days=200),
                "acquisition_cost": Decimal("650.00"),
                "current_value": Decimal("585.00"),
                "condition_status": "bueno",
                "custodian": custodians[2],
                "responsible_user": admin_user,
                "is_insured": True,
                "insurance_policy": electronic_policy,
            },
        ]

        created_assets = []
        for asset_data in assets_data:
            asset, created = Asset.objects.get_or_create(
                serial_number=asset_data["serial_number"], defaults=asset_data
            )
            if created:
                self.stdout.write(
                    f"   [+] Bien creado: {asset.asset_code} - {asset.name} -> Custodio: {asset.custodian.username}"
                )
            else:
                self.stdout.write(f"   [-] Bien existente: {asset.asset_code}")
            created_assets.append(asset)

        return created_assets

    def create_claims(self, assets, policies, users):
        """Create sample claims"""
        from claims.models import Claim, ClaimTimeline

        self.stdout.write("[*] Creando siniestros...")

        # Get insured assets
        insured_assets = [a for a in assets if a.is_insured and a.insurance_policy]

        if not insured_assets:
            self.stdout.write(
                self.style.WARNING(
                    "   [!] No hay bienes asegurados para crear siniestros"
                )
            )
            return []

        today = timezone.now().date()

        claims_data = [
            {
                "asset": insured_assets[0],
                "fecha_siniestro": today - timedelta(days=15),
                "incident_date": today - timedelta(days=15),
                "causa": "Colisión vehicular en vía pública",
                "ubicacion_detallada": "Av. Manuel Agustín Aguirre, frente a UTPL Campus Central",
                "incident_location": "Av. Manuel Agustín Aguirre, Loja",
                "incident_description": "El vehículo sufrió daños en la parte frontal debido a colisión con otro vehículo en una intersección",
                "estimated_loss": Decimal("5500.00"),
                "status": "pendiente",
            },
            {
                "asset": (
                    insured_assets[2] if len(insured_assets) > 2 else insured_assets[0]
                ),
                "fecha_siniestro": today - timedelta(days=10),
                "incident_date": today - timedelta(days=10),
                "causa": "Falla eléctrica por sobrevoltaje",
                "ubicacion_detallada": "Oficina 305, Edificio de TI, Campus UTPL",
                "incident_location": "Edificio TI - Oficina 305",
                "incident_description": "La impresora dejó de funcionar después de una descarga eléctrica durante una tormenta",
                "estimated_loss": Decimal("500.00"),
                "status": "en_revision",
            },
            {
                "asset": (
                    insured_assets[3] if len(insured_assets) > 3 else insured_assets[0]
                ),
                "fecha_siniestro": today - timedelta(days=5),
                "incident_date": today - timedelta(days=5),
                "causa": "Robo de equipo",
                "ubicacion_detallada": "Laboratorio de Computación 2, Segundo Piso, Edificio B",
                "incident_location": "Lab. Computación 2 - Edificio B",
                "incident_description": "Se reporta robo de computador durante el fin de semana. Se encontró la ventana forzada",
                "estimated_loss": Decimal("1200.00"),
                "status": "requiere_cambios",
                "validation_comments": "Por favor adjuntar denuncia policial y fotos del lugar del incidente",
            },
        ]

        created_claims = []
        for claim_data in claims_data:
            asset = claim_data.pop("asset")

            # Set additional required fields
            claim_data["policy"] = asset.insurance_policy
            claim_data["reportante"] = asset.custodian
            claim_data["reported_by"] = asset.custodian
            claim_data["asset_type"] = asset.asset_type
            claim_data["asset_description"] = asset.name
            claim_data["asset_code"] = asset.asset_code
            claim_data["asset"] = asset

            claim = Claim(**claim_data)
            claim.save()

            # Create timeline entry
            ClaimTimeline.objects.create(
                claim=claim,
                event_type="claim_created",
                event_description="Siniestro reportado por el custodio",
                created_by=asset.custodian,
            )

            self.stdout.write(
                f"   [+] Siniestro creado: {claim.claim_number} - {claim.get_status_display()}"
            )
            created_claims.append(claim)

        return created_claims

    def print_summary(self, users, companies, brokers, policies, assets, claims):
        """Print summary of created data"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("RESUMEN DE DATOS CREADOS"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Usuarios: {len(users)}")
        self.stdout.write(f"Companias de Seguros: {len(companies)}")
        self.stdout.write(f"Corredores: {len(brokers)}")
        self.stdout.write(f"Polizas: {len(policies)}")
        self.stdout.write(f"Bienes/Activos: {len(assets)}")
        self.stdout.write(f"Siniestros: {len(claims)}")
        self.stdout.write("=" * 60)

        self.stdout.write("\n" + self.style.WARNING("CREDENCIALES DE ACCESO:"))
        self.stdout.write("-" * 60)
        for user in users:
            role_display = user.get_role_display()
            password = (
                "Admin123!"
                if user.role == "admin"
                else (
                    "Gerente123!"
                    if user.role == "insurance_manager"
                    else "Custodio123!"
                )
            )
            self.stdout.write(f"  {user.username:20} | {password:15} | {role_display}")
        self.stdout.write("-" * 60)
