"""
Create Assets and assign to specific custodians
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import UserProfile
from assets.models import Asset


class Command(BaseCommand):
    help = "Create assets and assign to custodians"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🚀 Creando bienes y asignando a custodios...")
        )

        # Get admin and custodians
        admin = UserProfile.objects.filter(role="admin").first()
        custodians = {
            "ana": UserProfile.objects.filter(username="ana.garcia").first(),
            "pedro": UserProfile.objects.filter(username="pedro.martinez").first(),
            "lucia": UserProfile.objects.filter(username="lucia.rodriguez").first(),
        }

        # Validate users exist
        if not admin:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Error: No se encontró el usuario "admin". Ejecuta populate_step1 primero.'
                )
            )
            return

        missing_custodians = [name for name, user in custodians.items() if not user]
        if missing_custodians:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error: Faltan custodios: {", ".join(missing_custodians)}. Ejecuta populate_step1 primero.'
                )
            )
            return

        try:
            with transaction.atomic():
                assets = []
                today = date.today()

                # Assets for Ana Garcia (Sistemas)
                ana_assets = [
                    {
                        "type": "equipo_electronico",
                        "brand": "Dell",
                        "model": "OptiPlex 7090",
                        "value": "1500.00",
                    },
                    {
                        "type": "equipo_electronico",
                        "brand": "HP",
                        "model": "EliteBook 840",
                        "value": "1800.00",
                    },
                    {
                        "type": "equipo_electronico",
                        "brand": "Dell",
                        "model": "PowerEdge R750",
                        "value": "5000.00",
                    },
                    {
                        "type": "equipo_electronico",
                        "brand": "Cisco",
                        "model": "Catalyst 9300",
                        "value": "2500.00",
                    },
                    {
                        "type": "equipo_electronico",
                        "brand": "HP",
                        "model": "LaserJet Pro",
                        "value": "800.00",
                    },
                ]

                # Assets for Pedro Martinez (Infraestructura)
                pedro_assets = [
                    {
                        "type": "equipo_electronico",
                        "brand": "Epson",
                        "model": "PowerLite L610U",
                        "value": "2000.00",
                    },
                    {
                        "type": "maquinaria",
                        "brand": "LG",
                        "model": "Dual Inverter",
                        "value": "1200.00",
                    },
                    {
                        "type": "mobiliario",
                        "brand": "Muebles Modernos",
                        "model": "Ejecutivo",
                        "value": "600.00",
                    },
                    {
                        "type": "mobiliario",
                        "brand": "Ergonómica Pro",
                        "model": "Executive Plus",
                        "value": "400.00",
                    },
                    {
                        "type": "equipo_electronico",
                        "brand": "Lenovo",
                        "model": "ThinkCentre",
                        "value": "1400.00",
                    },
                ]

                # Assets for Lucia Rodriguez (Laboratorios)
                lucia_assets = [
                    {
                        "type": "equipo_electronico",
                        "brand": "Olympus",
                        "model": "CX43",
                        "value": "3500.00",
                    },
                    {
                        "type": "equipo_electronico",
                        "brand": "Dell",
                        "model": "Latitude 5420",
                        "value": "1700.00",
                    },
                    {
                        "type": "equipo_electronico",
                        "brand": "Canon",
                        "model": "imageRUNNER",
                        "value": "900.00",
                    },
                    {
                        "type": "equipo_electronico",
                        "brand": "Epson",
                        "model": "EB-X41",
                        "value": "1500.00",
                    },
                    {
                        "type": "equipo_electronico",
                        "brand": "HP",
                        "model": "ProDesk 600",
                        "value": "1600.00",
                    },
                ]

                # Create assets for each custodian
                asset_counter = 1

                # --- Ana Assets ---
                for asset_data in ana_assets:
                    val = Decimal(asset_data["value"])
                    curr_val = (val * Decimal("0.8")).quantize(Decimal("0.01"))

                    asset = Asset.objects.create(
                        asset_code=f"ASSET-{str(asset_counter).zfill(5)}",
                        name=f'{asset_data["brand"]} {asset_data["model"]}',
                        description=f'Equipo asignado a Sistemas: {asset_data["brand"]} {asset_data["model"]}',
                        brand=asset_data["brand"],
                        model=asset_data["model"],
                        serial_number=f"SN{100000 + asset_counter}",
                        asset_type=asset_data["type"],
                        location="Departamento de Sistemas",
                        acquisition_date=today - timedelta(days=365),
                        acquisition_cost=val,
                        current_value=curr_val,
                        custodian=custodians["ana"],
                        responsible_user=admin,
                        is_insured=False,
                        condition_status="bueno",
                    )
                    assets.append(asset)
                    self.stdout.write(
                        f"  ✓ {asset.asset_code}: {asset.name} → Ana García (Sistemas)"
                    )
                    asset_counter += 1

                # --- Pedro Assets ---
                for asset_data in pedro_assets:
                    val = Decimal(asset_data["value"])
                    curr_val = (val * Decimal("0.8")).quantize(Decimal("0.01"))

                    asset = Asset.objects.create(
                        asset_code=f"ASSET-{str(asset_counter).zfill(5)}",
                        name=f'{asset_data["brand"]} {asset_data["model"]}',
                        description=f'Equipo asignado a Infraestructura: {asset_data["brand"]} {asset_data["model"]}',
                        brand=asset_data["brand"],
                        model=asset_data["model"],
                        serial_number=f"SN{100000 + asset_counter}",
                        asset_type=asset_data["type"],
                        location="Departamento de Infraestructura",
                        acquisition_date=today - timedelta(days=365),
                        acquisition_cost=val,
                        current_value=curr_val,
                        custodian=custodians["pedro"],
                        responsible_user=admin,
                        is_insured=False,
                        condition_status="bueno",
                    )
                    assets.append(asset)
                    self.stdout.write(
                        f"  ✓ {asset.asset_code}: {asset.name} → Pedro Martínez (Infraestructura)"
                    )
                    asset_counter += 1

                # --- Lucia Assets ---
                for asset_data in lucia_assets:
                    val = Decimal(asset_data["value"])
                    curr_val = (val * Decimal("0.8")).quantize(Decimal("0.01"))

                    asset = Asset.objects.create(
                        asset_code=f"ASSET-{str(asset_counter).zfill(5)}",
                        name=f'{asset_data["brand"]} {asset_data["model"]}',
                        description=f'Equipo asignado a Laboratorios: {asset_data["brand"]} {asset_data["model"]}',
                        brand=asset_data["brand"],
                        model=asset_data["model"],
                        serial_number=f"SN{100000 + asset_counter}",
                        asset_type=asset_data["type"],
                        location="Laboratorios",
                        acquisition_date=today - timedelta(days=365),
                        acquisition_cost=val,
                        current_value=curr_val,
                        custodian=custodians["lucia"],
                        responsible_user=admin,
                        is_insured=False,
                        condition_status="bueno",
                    )
                    assets.append(asset)
                    self.stdout.write(
                        f"  ✓ {asset.asset_code}: {asset.name} → Lucía Rodríguez (Laboratorios)"
                    )
                    asset_counter += 1

                self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {len(assets)} bienes creados y asignados!")
                )
                self.stdout.write(self.style.SUCCESS("=" * 70))

                # Summary by custodian
                self.stdout.write(self.style.SUCCESS("\n📊 RESUMEN POR CUSTODIO:"))
                self.stdout.write(
                    f"\n👤 Ana García (Sistemas): {len(ana_assets)} bienes"
                )
                self.stdout.write(
                    f"👤 Pedro Martínez (Infraestructura): {len(pedro_assets)} bienes"
                )
                self.stdout.write(
                    f"👤 Lucía Rodríguez (Laboratorios): {len(lucia_assets)} bienes"
                )

                self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
                self.stdout.write(
                    self.style.WARNING("💡 Nota: Los bienes no tienen póliza asignada.")
                )
                self.stdout.write(
                    self.style.WARNING("   Puedes asignarles pólizas desde el admin.")
                )
                self.stdout.write(self.style.SUCCESS("=" * 70 + "\n"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {str(e)}"))
            import traceback

            self.stdout.write(self.style.ERROR(traceback.format_exc()))
