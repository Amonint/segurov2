#!/usr/bin/env python
"""
Script para poblar la base de datos con datos ficticios de prueba
Ejecutar con: python manage.py shell < populate_data.py
"""

import os
import django
import random
from decimal import Decimal
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seguros.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from companies.models import InsuranceCompany, EmissionRights
from brokers.models import Broker
from policies.models import Policy
from assets.models import Asset
from claims.models import Claim
from invoices.models import Invoice
from notifications.models import Notification

User = get_user_model()

def create_companies():
    """Crear compañías aseguradoras"""
    print("Creando compañías aseguradoras...")

    companies_data = [
        {
            'name': 'Seguros Pichincha',
            'ruc': '1790012345001',
            'address': 'Av. Amazonas N32-146 y Av. República, Quito',
            'phone': '23966500',
            'email': 'contacto@segurospichincha.com',
            'contact_person': 'María González'
        },
        {
            'name': 'Seguros Sucre',
            'ruc': '1790012346001',
            'address': 'Av. 6 de Diciembre N24-99 y Av. Patria, Quito',
            'phone': '24320000',
            'email': 'info@segurosucre.com',
            'contact_person': 'Carlos Rodríguez'
        },
        {
            'name': 'Seguros del Pichincha',
            'ruc': '1790012347001',
            'address': 'Av. Amazonas N24-22 y Jorge Washington, Quito',
            'phone': '24301000',
            'email': 'ventas@segurospichincha.com.ec',
            'contact_person': 'Ana López'
        },
        {
            'name': 'Seguros Equinoccial',
            'ruc': '1790012348001',
            'address': 'Av. República de El Salvador N34-376, Quito',
            'phone': '22456789',
            'email': 'contacto@equinoccial.com.ec',
            'contact_person': 'Pedro Martínez'
        },
        {
            'name': 'Seguros Rocafuerte',
            'ruc': '1790012349001',
            'address': 'Av. 10 de Agosto N34-156, Guayaquil',
            'phone': '42345678',
            'email': 'info@rocauerte.com.ec',
            'contact_person': 'Laura Sánchez'
        }
    ]

    companies = []
    for data in companies_data:
        company, created = InsuranceCompany.objects.get_or_create(
            ruc=data['ruc'],
            defaults=data
        )
        companies.append(company)
        if created:
            print(f"  ✓ Creada compañía: {company.name}")

    return companies

def create_emission_rights():
    """Crear tabla de derechos de emisión"""
    print("Creando tabla de derechos de emisión...")

    # Limpiar datos existentes
    EmissionRights.objects.all().delete()

    emission_data = [
        {'min_amount': 0, 'max_amount': 1000, 'emission_right': 5},
        {'min_amount': 1000, 'max_amount': 5000, 'emission_right': 10},
        {'min_amount': 5000, 'max_amount': 10000, 'emission_right': 15},
        {'min_amount': 10000, 'max_amount': 50000, 'emission_right': 25},
        {'min_amount': 50000, 'max_amount': 100000, 'emission_right': 50},
        {'min_amount': 100000, 'max_amount': 999999999, 'emission_right': 75},
    ]

    # Crear usando bulk_create para evitar validaciones durante la creación
    rights = []
    for data in emission_data:
        right = EmissionRights(
            min_amount=data['min_amount'],
            max_amount=data['max_amount'],
            emission_right=data['emission_right']
        )
        rights.append(right)
        print(f"  ✓ Creado derecho de emisión: {data['min_amount']}-{data['max_amount']} = ${data['emission_right']}")

    # Usar bulk_create para insertar todos de una vez
    EmissionRights.objects.bulk_create(rights)

def create_brokers():
    """Crear corredores"""
    print("Creando corredores...")

    brokers_data = [
        {
            'name': 'Corredores Unidos',
            'ruc': '1790023450001',
            'commission_percentage': 5.0,
            'contact_person': 'Roberto Silva',
            'phone': '28001234',
            'email': 'roberto@corredoresunidos.com'
        },
        {
            'name': 'Asesores Financieros',
            'ruc': '1790023451001',
            'commission_percentage': 7.5,
            'contact_person': 'María Torres',
            'phone': '28005678',
            'email': 'maria@asesoresfinancieros.com'
        },
        {
            'name': 'Consultores de Riesgo',
            'ruc': '1790023452001',
            'commission_percentage': 6.0,
            'contact_person': 'Juan Pérez',
            'phone': '28003456',
            'email': 'juan@consultoresderiesgo.com'
        }
    ]

    brokers = []
    for data in brokers_data:
        broker, created = Broker.objects.get_or_create(
            ruc=data['ruc'],
            defaults=data
        )
        brokers.append(broker)
        if created:
            print(f"  ✓ Creado corredor: {broker.name}")

    return brokers

def create_users():
    """Crear usuarios de prueba"""
    print("Creando usuarios de prueba...")

    users_data = [
        {
            'username': 'admin',
            'email': 'admin@utpl.edu.ec',
            'first_name': 'Administrador',
            'last_name': 'del Sistema',
            'role': 'admin',
            'department': 'TI'
        },
        {
            'username': 'gerente_seguros',
            'email': 'gerente@utpl.edu.ec',
            'first_name': 'María',
            'last_name': 'González',
            'role': 'insurance_manager',
            'department': 'Seguros'
        },
        {
            'username': 'analista_financiero',
            'email': 'analista@utpl.edu.ec',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'role': 'financial_analyst',
            'department': 'Finanzas'
        },
        {
            'username': 'consultor',
            'email': 'consultor@utpl.edu.ec',
            'first_name': 'Ana',
            'last_name': 'López',
            'role': 'consultant',
            'department': 'Consultoría'
        },
        {
            'username': 'custodio1',
            'email': 'custodio1@utpl.edu.ec',
            'first_name': 'Pedro',
            'last_name': 'Martínez',
            'role': 'requester',
            'department': 'Facultad de Ingeniería'
        },
        {
            'username': 'custodio2',
            'email': 'custodio2@utpl.edu.ec',
            'first_name': 'Laura',
            'last_name': 'Sánchez',
            'role': 'requester',
            'department': 'Facultad de Ciencias Administrativas'
        },
        {
            'username': 'custodio3',
            'email': 'custodio3@utpl.edu.ec',
            'first_name': 'Roberto',
            'last_name': 'Silva',
            'role': 'requester',
            'department': 'Biblioteca Central'
        }
    ]

    users = []
    for data in users_data:
        # Verificar si el usuario ya existe
        if UserProfile.objects.filter(username=data['username']).exists():
            user = UserProfile.objects.get(username=data['username'])
            print(f"  ✓ Usuario ya existe: {user.username}")
        else:
            # Crear usuario con create_user que maneja la contraseña correctamente
            user = UserProfile.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='password123',
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=data['role'],
                department=data['department'],
                full_name=f"{data['first_name']} {data['last_name']}",
                is_active=True
            )
            print(f"  ✓ Creado usuario: {user.username} ({user.get_role_display()})")
        users.append(user)

    return users

def create_policies(companies, brokers, users):
    """Crear pólizas de prueba"""
    print("Creando pólizas de prueba...")

    policy_data = [
        {
            'policy_number': 'POL-2024-0001',
            'insurance_company': companies[0],
            'broker': random.choice(brokers) if random.random() > 0.3 else None,
            'group_type': 'patrimoniales',
            'subgroup': 'Edificios',
            'branch': 'Incendio',
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today() + timedelta(days=335),
            'insured_value': Decimal('500000.00'),
            'responsible_user': users[1]  # gerente_seguros
        },
        {
            'policy_number': 'POL-2024-0002',
            'insurance_company': companies[1],
            'broker': random.choice(brokers) if random.random() > 0.3 else None,
            'group_type': 'personas',
            'subgroup': 'Vida Individual',
            'branch': 'Vida',
            'start_date': date.today() - timedelta(days=15),
            'end_date': date.today() + timedelta(days=350),
            'insured_value': Decimal('100000.00'),
            'responsible_user': users[1]
        },
        {
            'policy_number': 'POL-2024-0003',
            'insurance_company': companies[2],
            'broker': brokers[0],
            'group_type': 'patrimoniales',
            'subgroup': 'Vehículos',
            'branch': 'Automóviles',
            'start_date': date.today() - timedelta(days=60),
            'end_date': date.today() + timedelta(days=305),
            'insured_value': Decimal('25000.00'),
            'responsible_user': users[1]
        },
        {
            'policy_number': 'POL-2024-0004',
            'insurance_company': companies[3],
            'broker': brokers[1],
            'group_type': 'patrimoniales',
            'subgroup': 'Equipos Electrónicos',
            'branch': 'Robo',
            'start_date': date.today() - timedelta(days=10),
            'end_date': date.today() + timedelta(days=355),
            'insured_value': Decimal('150000.00'),
            'responsible_user': users[1]
        },
        {
            'policy_number': 'POL-2024-0005',
            'insurance_company': companies[4],
            'broker': None,
            'group_type': 'patrimoniales',
            'subgroup': 'Maquinaria',
            'branch': 'Daños',
            'start_date': date.today() - timedelta(days=45),
            'end_date': date.today() + timedelta(days=320),
            'insured_value': Decimal('300000.00'),
            'responsible_user': users[1]
        }
    ]

    policies = []
    for data in policy_data:
        policy, created = Policy.objects.get_or_create(
            policy_number=data['policy_number'],
            defaults=data
        )
        policies.append(policy)
        if created:
            print(f"  ✓ Creada póliza: {policy.policy_number} - {policy.insurance_company.name}")

    return policies

def create_assets(policies, users):
    """Crear bienes/activos"""
    print("Creando bienes/activos...")

    assets_data = [
        {
            'asset_code': 'ACT-2024-0001',
            'name': 'Servidor Dell PowerEdge R440',
            'description': 'Servidor para laboratorio de redes',
            'asset_type': 'equipo_electronico',
            'location': 'Laboratorio de Redes - Bloque A',
            'acquisition_date': date.today() - timedelta(days=180),
            'acquisition_cost': Decimal('8500.00'),
            'current_value': Decimal('6800.00'),
            'condition_status': 'bueno',
            'custodian': users[4],  # custodio1
            'responsible_user': users[1],  # gerente_seguros
            'is_insured': True,
            'insurance_policy': policies[3] if len(policies) > 3 else None
        },
        {
            'asset_code': 'ACT-2024-0002',
            'name': 'Toyota Corolla 2020',
            'description': 'Vehículo oficial de la rectoría',
            'asset_type': 'vehiculo',
            'location': 'Parqueadero Principal',
            'acquisition_date': date.today() - timedelta(days=365),
            'acquisition_cost': Decimal('18000.00'),
            'current_value': Decimal('14400.00'),
            'condition_status': 'excelente',
            'custodian': users[5],  # custodio2
            'responsible_user': users[1],
            'is_insured': True,
            'insurance_policy': policies[2] if len(policies) > 2 else None
        },
        {
            'asset_code': 'ACT-2024-0003',
            'name': 'Proyector Epson EB-S41',
            'description': 'Proyector para auditorio principal',
            'asset_type': 'equipo_electronico',
            'location': 'Auditorio Principal - Planta Baja',
            'acquisition_date': date.today() - timedelta(days=90),
            'acquisition_cost': Decimal('1200.00'),
            'current_value': Decimal('960.00'),
            'condition_status': 'bueno',
            'custodian': users[6],  # custodio3
            'responsible_user': users[1],
            'is_insured': True,
            'insurance_policy': policies[3] if len(policies) > 3 else None
        },
        {
            'asset_code': 'ACT-2024-0004',
            'name': 'Impresora HP LaserJet MFP M182nw',
            'description': 'Multifuncional para oficina administrativa',
            'asset_type': 'equipo_electronico',
            'location': 'Oficina Administrativa - Segundo Piso',
            'acquisition_date': date.today() - timedelta(days=60),
            'acquisition_cost': Decimal('450.00'),
            'current_value': Decimal('360.00'),
            'condition_status': 'excelente',
            'custodian': users[5],  # custodio2
            'responsible_user': users[1],
            'is_insured': False,
            'insurance_policy': None
        },
        {
            'asset_code': 'ACT-2024-0005',
            'name': 'Biblioteca Digital',
            'description': 'Colección de libros electrónicos y bases de datos',
            'asset_type': 'inventario',
            'location': 'Biblioteca Central',
            'acquisition_date': date.today() - timedelta(days=30),
            'acquisition_cost': Decimal('25000.00'),
            'current_value': Decimal('25000.00'),
            'condition_status': 'excelente',
            'custodian': users[6],  # custodio3
            'responsible_user': users[1],
            'is_insured': True,
            'insurance_policy': policies[0] if len(policies) > 0 else None
        }
    ]

    assets = []
    for data in assets_data:
        asset, created = Asset.objects.get_or_create(
            asset_code=data['asset_code'],
            defaults=data
        )
        assets.append(asset)
        if created:
            print(f"  ✓ Creado activo: {asset.asset_code} - {asset.name}")

    return assets

def create_claims(policies, users):
    """Crear siniestros de prueba"""
    print("Creando siniestros de prueba...")

    claims_data = [
        {
            'claim_number': 'SIN-2024-0001',
            'policy': policies[2] if len(policies) > 2 else None,
            'incident_date': date.today() - timedelta(days=5),
            'report_date': date.today() - timedelta(days=3),
            'incident_location': 'Parqueadero Principal',
            'incident_description': 'Daño en vehículo oficial por colisión menor',
            'asset_type': 'Vehículo',
            'asset_description': 'Toyota Corolla 2020',
            'asset_code': 'ACT-2024-0002',
            'estimated_loss': Decimal('1200.00'),
            'status': 'under_evaluation',
            'reported_by': users[5],  # custodio2
            'assigned_to': users[1]   # gerente_seguros
        },
        {
            'claim_number': 'SIN-2024-0002',
            'policy': policies[3] if len(policies) > 3 else None,
            'incident_date': date.today() - timedelta(days=10),
            'report_date': date.today() - timedelta(days=8),
            'incident_location': 'Laboratorio de Redes',
            'incident_description': 'Daño por corto circuito en servidor',
            'asset_type': 'Equipo Electrónico',
            'asset_description': 'Servidor Dell PowerEdge R440',
            'asset_code': 'ACT-2024-0001',
            'estimated_loss': Decimal('800.00'),
            'status': 'liquidated',
            'approved_amount': Decimal('650.00'),
            'reported_by': users[4],  # custodio1
            'assigned_to': users[1]
        },
        {
            'claim_number': 'SIN-2024-0003',
            'policy': policies[3] if len(policies) > 3 else None,
            'incident_date': date.today() - timedelta(days=15),
            'report_date': date.today() - timedelta(days=12),
            'incident_location': 'Auditorio Principal',
            'incident_description': 'Robo de proyector durante evento académico',
            'asset_type': 'Equipo Electrónico',
            'asset_description': 'Proyector Epson EB-S41',
            'asset_code': 'ACT-2024-0003',
            'estimated_loss': Decimal('1200.00'),
            'status': 'paid',
            'approved_amount': Decimal('1200.00'),
            'payment_date': date.today() - timedelta(days=2),
            'reported_by': users[6],  # custodio3
            'assigned_to': users[1]
        }
    ]

    claims = []
    for data in claims_data:
        claim, created = Claim.objects.get_or_create(
            claim_number=data['claim_number'],
            defaults=data
        )
        claims.append(claim)
        if created:
            print(f"  ✓ Creado siniestro: {claim.claim_number} - {claim.incident_description[:50]}...")

    return claims

def create_invoices(policies, users):
    """Crear facturas de prueba"""
    print("Creando facturas de prueba...")

    invoices = []
    for i, policy in enumerate(policies):
        invoice_number = f'INV-2024-{i+1:04d}'

        # Calcular fechas
        invoice_date = policy.start_date
        due_date = invoice_date + timedelta(days=30)

        # Calcular valores manualmente para evitar problemas de decimales
        premium = (policy.insured_value * Decimal('0.01')).quantize(Decimal('0.01'))  # 1% del valor asegurado
        superintendence_contribution = (premium * Decimal('0.035')).quantize(Decimal('0.01'))
        farm_insurance_contribution = (premium * Decimal('0.005')).quantize(Decimal('0.01'))
        emission_rights = EmissionRights.get_emission_right(premium)
        tax_base = (premium + superintendence_contribution + farm_insurance_contribution + emission_rights).quantize(Decimal('0.01'))
        iva = (tax_base * Decimal('0.15')).quantize(Decimal('0.01'))
        withholding_tax = Decimal('0.00')
        total_amount = (tax_base + iva - withholding_tax).quantize(Decimal('0.01'))

        # Crear factura directamente para evitar cálculos automáticos
        payment_status = random.choice(['pending', 'paid', 'paid', 'paid'])

        invoice = Invoice(
            invoice_number=invoice_number,
            policy=policy,
            invoice_date=invoice_date,
            due_date=due_date,
            premium=premium,
            superintendence_contribution=superintendence_contribution,
            farm_insurance_contribution=farm_insurance_contribution,
            emission_rights=emission_rights,
            tax_base=tax_base,
            iva=iva,
            withholding_tax=withholding_tax,
            total_amount=total_amount,
            payment_status=payment_status,
            created_by=users[2]  # analista_financiero
        )

        # Si está pagada, agregar fecha de pago
        if payment_status == 'paid':
            invoice.payment_date = invoice_date + timedelta(days=random.randint(1, 20))

        # Guardar sin ejecutar cálculos automáticos
        invoice.save()
        print(f"  ✓ Creada factura: {invoice.invoice_number} - ${invoice.total_amount:.2f} ({invoice.get_payment_status_display()})")
        invoices.append(invoice)

    return invoices

def create_notifications(users):
    """Crear notificaciones de prueba"""
    print("Creando notificaciones de prueba...")

    notifications_data = [
        {
            'user': users[0],  # admin
            'notification_type': 'alert',
            'title': 'Sistema Actualizado',
            'message': 'El sistema de seguros ha sido actualizado con nuevas funcionalidades.',
            'priority': 'normal',
            'is_read': False
        },
        {
            'user': users[1],  # gerente_seguros
            'notification_type': 'policy_expiring',
            'title': 'Póliza Próxima a Vencer',
            'message': 'La póliza POL-2024-0001 vence en 30 días.',
            'priority': 'high',
            'is_read': False
        },
        {
            'user': users[2],  # analista_financiero
            'notification_type': 'payment_due',
            'title': 'Pago Pendiente',
            'message': 'La factura INV-2024-0001 vence en 15 días.',
            'priority': 'urgent',
            'is_read': False
        },
        {
            'user': users[4],  # custodio1
            'notification_type': 'claim_update',
            'title': 'Actualización de Siniestro',
            'message': 'Su siniestro SIN-2024-0002 ha sido liquidado.',
            'priority': 'normal',
            'is_read': True
        },
        {
            'user': users[5],  # custodio2
            'notification_type': 'document_required',
            'title': 'Documentos Requeridos',
            'message': 'Se requieren fotos adicionales para el siniestro SIN-2024-0001.',
            'priority': 'high',
            'is_read': False
        }
    ]

    notifications = []
    for data in notifications_data:
        notification, created = Notification.objects.get_or_create(
            user=data['user'],
            notification_type=data['notification_type'],
            title=data['title'],
            defaults=data
        )
        notifications.append(notification)
        if created:
            print(f"  ✓ Creada notificación: {notification.title} para {notification.user.username}")

    return notifications

def clear_existing_data():
    """Limpiar datos existentes para asegurar una población limpia"""
    print("🧹 Limpiando datos existentes...")

    # Eliminar en orden inverso de dependencias
    Notification.objects.all().delete()
    Claim.objects.all().delete()
    Invoice.objects.all().delete()
    Asset.objects.all().delete()
    Policy.objects.all().delete()
    Broker.objects.all().delete()
    InsuranceCompany.objects.all().delete()
    EmissionRights.objects.all().delete()
    UserProfile.objects.filter(is_superuser=False).delete()  # Mantener superusuario si existe

    print("  ✓ Datos existentes eliminados")

def main():
    """Función principal para poblar la base de datos"""
    print("🚀 Iniciando población de datos ficticios...")
    print("=" * 50)

    try:
        # Limpiar datos existentes primero
        clear_existing_data()
        print()
        # Crear datos en orden de dependencias
        companies = create_companies()
        create_emission_rights()
        brokers = create_brokers()
        users = create_users()
        policies = create_policies(companies, brokers, users)
        assets = create_assets(policies, users)
        claims = create_claims(policies, users)
        invoices = create_invoices(policies, users)
        notifications = create_notifications(users)

        print("=" * 50)
        print("✅ ¡Base de datos poblada exitosamente!")
        print(f"   • {len(companies)} compañías aseguradoras")
        print(f"   • {len(brokers)} corredores")
        print(f"   • {len(users)} usuarios")
        print(f"   • {len(policies)} pólizas")
        print(f"   • {len(assets)} activos/bienes")
        print(f"   • {len(claims)} siniestros")
        print(f"   • {len(invoices)} facturas")
        print(f"   • {len(notifications)} notificaciones")
        print()
        print("🔐 Credenciales de acceso:")
        print("   Administrador: admin / password123")
        print("   Gerente de Seguros: gerente_seguros / password123")
        print("   Analista Financiero: analista_financiero / password123")
        print("   Consultor: consultor / password123")
        print("   Custodios: custodio1, custodio2, custodio3 / password123")
        print()
        print("🌐 URL del sistema: http://localhost:8000")

    except Exception as e:
        print(f"❌ Error durante la población: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
