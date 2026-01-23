"""
Simplified script - creates only users, companies, and brokers
"""

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import UserProfile
from brokers.models import Broker
from companies.models import InsuranceCompany


class Command(BaseCommand):
    help = "Populate database - Step 1: Users, Companies, Brokers"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🚀 Poblando usuarios, compañías y corredores...")
        )

        try:
            with transaction.atomic():
                # Users
                self.stdout.write("Creando usuarios...")
                users = self.create_users()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {len(users)} usuarios creados")
                )

                # Companies
                self.stdout.write("Creando compañías...")
                companies = self.create_companies()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {len(companies)} compañías creadas")
                )

                # Brokers
                self.stdout.write("Creando corredores...")
                brokers = self.create_brokers()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {len(brokers)} corredores creados")
                )

            self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
            self.stdout.write(self.style.SUCCESS("✅ Paso 1 completado!"))
            self.stdout.write(self.style.SUCCESS("=" * 70))
            self.print_credentials()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {str(e)}"))
            import traceback

            self.stdout.write(self.style.ERROR(traceback.format_exc()))

    def create_users(self):
        """Create test users"""
        users = []

        # Admin
        try:
            admin = UserProfile.objects.get(username="admin")
        except UserProfile.DoesNotExist:
            admin = UserProfile.objects.create_superuser(
                username="admin",
                email="admin@utpl.edu.ec",
                password="admin123",
                first_name="Admin",
                last_name="Sistema",
            )
        admin.role = "admin"
        admin.department = "Administración"
        admin.save()
        users.append(admin)

        # Managers
        for name in [("Maria", "Lopez"), ("Juan", "Perez")]:
            username = f"{name[0].lower()}.{name[1].lower()}"
            try:
                user = UserProfile.objects.get(username=username)
            except UserProfile.DoesNotExist:
                user = UserProfile.objects.create_user(
                    username=username,
                    email=f"{username}@utpl.edu.ec",
                    password="manager123",
                    first_name=name[0],
                    last_name=name[1],
                )
            user.role = "insurance_manager"
            user.department = "Seguros"
            user.save()
            users.append(user)

        # Custodians
        for i, name in enumerate(
            [("Ana", "Garcia"), ("Pedro", "Martinez"), ("Lucia", "Rodriguez")]
        ):
            username = f"{name[0].lower()}.{name[1].lower()}"
            try:
                user = UserProfile.objects.get(username=username)
            except UserProfile.DoesNotExist:
                user = UserProfile.objects.create_user(
                    username=username,
                    email=f"{username}@utpl.edu.ec",
                    password="custodian123",
                    first_name=name[0],
                    last_name=name[1],
                )
            user.role = "requester"
            user.department = ["Sistemas", "Infraestructura", "Laboratorios"][i]
            user.save()
            users.append(user)

        return users

    def create_companies(self):
        """Create insurance companies"""
        companies = []
        for name in ["Seguros Equinoccial", "Seguros Sucre", "Latina Seguros"]:
            company, _ = InsuranceCompany.objects.get_or_create(
                name=name,
                defaults={
                    "ruc": f"179{random.randint(1000000, 9999999)}001",
                    "address": "Quito, Ecuador",
                    "phone": "+593 2 298 3800",
                    "email": f'info@{name.lower().replace(" ", "")}.com',
                },
            )
            companies.append(company)
        return companies

    def create_brokers(self):
        """Create brokers"""
        brokers = []
        for name in ["Corredores Asociados", "Broker Ecuador"]:
            broker, _ = Broker.objects.get_or_create(
                name=name,
                defaults={
                    "ruc": f"179{random.randint(1000000, 9999999)}001",
                    "address": "Quito, Ecuador",
                    "phone": "+593 2 245 6789",
                    "email": f'info@{name.lower().replace(" ", "")}.com',
                    "commission_percentage": Decimal("5.00"),
                },
            )
            brokers.append(broker)
        return brokers

    def print_credentials(self):
        """Print login credentials"""
        self.stdout.write(self.style.SUCCESS("\n📋 CREDENCIALES DE ACCESO"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.WARNING("\n👤 ADMINISTRADOR:"))
        self.stdout.write("   Usuario: admin")
        self.stdout.write("   Contraseña: admin123")
        self.stdout.write(self.style.WARNING("\n👥 GERENTES:"))
        self.stdout.write("   Usuarios: maria.lopez / juan.perez")
        self.stdout.write("   Contraseña: manager123")
        self.stdout.write(self.style.WARNING("\n🔑 CUSTODIOS:"))
        self.stdout.write("   Usuarios: ana.garcia / pedro.martinez / lucia.rodriguez")
        self.stdout.write("   Contraseña: custodian123")
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(
            self.style.SUCCESS("🌐 Accede al sistema: http://127.0.0.1:8000")
        )
        self.stdout.write(
            self.style.WARNING(
                "\n💡 Ahora puedes crear pólizas, bienes y siniestros desde el admin"
            )
        )
        self.stdout.write(self.style.SUCCESS("=" * 70 + "\n"))
