#!/usr/bin/env python
"""
Script para crear plantillas de email básicas
Ejecutar con: python manage.py shell < create_email_templates.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seguros.settings')
django.setup()

from notifications.models import EmailTemplate

# Plantillas de email básicas
templates = [
    {
        'name': 'Notificación de Siniestro Reportado',
        'template_type': 'claim_reported',
        'recipient_type': 'broker',
        'subject': 'Nuevo Siniestro Reportado - {{claim_number}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">Nuevo Siniestro Reportado</h2>
            <p>Estimado broker,</p>
            <p>Se ha reportado un nuevo siniestro en el sistema:</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Número de Siniestro:</strong> {{claim_number}}<br>
                <strong>Póliza:</strong> {{policy_number}}<br>
                <strong>Fecha del Incidente:</strong> {{incident_date}}<br>
                <strong>Ubicación:</strong> {{incident_location}}<br>
                <strong>Descripción:</strong> {{incident_description}}<br>
                <strong>Pérdida Estimada:</strong> ${{estimated_loss}}
            </div>
            <p>Reportado por: {{reported_by}}</p>
            <p>Asignado a: {{assigned_to}}</p>
            <p>Por favor revise la documentación adjunta y proceda según corresponda.</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Confirmación de Reporte de Siniestro',
        'template_type': 'claim_reported',
        'recipient_type': 'user',
        'subject': 'Confirmación de Reporte - Siniestro {{claim_number}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #28a745;">Confirmación de Reporte de Siniestro</h2>
            <p>Estimado {{user_name}},</p>
            <p>Su reporte de siniestro ha sido registrado exitosamente:</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Número de Siniestro:</strong> {{claim_number}}<br>
                <strong>Póliza:</strong> {{policy_number}}<br>
                <strong>Fecha del Incidente:</strong> {{incident_date}}<br>
                <strong>Estado Actual:</strong> {{status}}
            </div>
            <p>Le mantendremos informado sobre cualquier actualización del proceso.</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Notificación de Póliza por Vencer',
        'template_type': 'policy_expiring',
        'recipient_type': 'user',
        'subject': 'Alerta: Póliza Próxima a Vencer',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ffc107;">Alerta de Vencimiento</h2>
            <p>Estimado {{user_name}},</p>
            <p>Le informamos que tiene una póliza próxima a vencer:</p>
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <strong>Número de Póliza:</strong> {{policy_number}}<br>
                <strong>Compañía:</strong> {{insurance_company}}<br>
                <strong>Fecha de Vencimiento:</strong> {{end_date}}<br>
                <strong>Días Restantes:</strong> {{days_remaining}}
            </div>
            <p>Le recomendamos renovar su póliza antes del vencimiento para mantener la cobertura continua.</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Notificación de Pago Pendiente',
        'template_type': 'payment_due',
        'recipient_type': 'user',
        'subject': 'Recordatorio: Pago Pendiente - Factura {{invoice_number}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #17a2b8;">Recordatorio de Pago</h2>
            <p>Estimado {{user_name}},</p>
            <p>Le recordamos que tiene un pago pendiente:</p>
            <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #17a2b8;">
                <strong>Número de Factura:</strong> {{invoice_number}}<br>
                <strong>Póliza:</strong> {{policy_number}}<br>
                <strong>Fecha de Vencimiento:</strong> {{due_date}}<br>
                <strong>Monto Total:</strong> ${{total_amount}}<br>
                <strong>Días Restantes:</strong> {{days_remaining}}
            </div>
            <p>Por favor realice el pago antes de la fecha de vencimiento para evitar intereses moratorios.</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Notificación de Póliza Vencida',
        'template_type': 'policy_expired',
        'recipient_type': 'user',
        'subject': 'Alerta: Póliza Vencida - {{policy_number}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">Póliza Vencida</h2>
            <p>Estimado/a,</p>
            <p>La siguiente póliza ha vencido:</p>
            <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Número de Póliza:</strong> {{policy_number}}<br>
                <strong>Compañía:</strong> {{company_name}}<br>
                <strong>Fecha de Vencimiento:</strong> {{expiry_date}}
            </div>
            <p>Puede revisar la póliza aquí: {{policy_url}}</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Notificación de Factura Vencida',
        'template_type': 'invoice_overdue',
        'recipient_type': 'user',
        'subject': 'Factura Vencida - {{invoice_number}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">Factura Vencida</h2>
            <p>Estimado/a,</p>
            <p>La siguiente factura está vencida:</p>
            <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Número de Factura:</strong> {{invoice_number}}<br>
                <strong>Monto:</strong> ${{amount}}<br>
                <strong>Días de atraso:</strong> {{days_overdue}}<br>
                <strong>Fecha de vencimiento:</strong> {{due_date}}
            </div>
            <p>Detalle: {{invoice_url}}</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Notificación de Siniestro Atrasado',
        'template_type': 'claim_overdue',
        'recipient_type': 'user',
        'subject': 'Siniestro Atrasado - {{claim_number}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ffc107;">Siniestro Atrasado</h2>
            <p>Estimado/a,</p>
            <p>El siguiente siniestro presenta retraso:</p>
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Número de Siniestro:</strong> {{claim_number}}<br>
                <strong>Póliza:</strong> {{policy_number}}<br>
                <strong>Días de atraso:</strong> {{days_overdue}}<br>
                <strong>Última actualización:</strong> {{last_update}}
            </div>
            <p>Detalle: {{claim_url}}</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Notificación de Documento Vencido',
        'template_type': 'document_overdue',
        'recipient_type': 'user',
        'subject': 'Documento Vencido - {{document_name}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">Documento Vencido</h2>
            <p>Estimado/a,</p>
            <p>El siguiente documento está vencido:</p>
            <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Documento:</strong> {{document_name}}<br>
                <strong>Siniestro:</strong> {{claim_number}}<br>
                <strong>Días de atraso:</strong> {{days_overdue}}<br>
                <strong>Fecha límite:</strong> {{deadline}}
            </div>
            <p>Detalle: {{claim_url}}</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Notificación de Mantenimiento Requerido',
        'template_type': 'maintenance_required',
        'recipient_type': 'user',
        'subject': 'Mantenimiento Requerido - {{asset_code}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #17a2b8;">Mantenimiento Requerido</h2>
            <p>Estimado/a,</p>
            <p>Se requiere mantenimiento para el siguiente activo:</p>
            <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Código:</strong> {{asset_code}}<br>
                <strong>Activo:</strong> {{asset_name}}<br>
                <strong>Condición:</strong> {{condition}}
            </div>
            <p>Detalle: {{asset_url}}</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Alerta del Sistema',
        'template_type': 'system_alert',
        'recipient_type': 'user',
        'subject': 'Alerta del Sistema - {{alert_name}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #6c757d;">Alerta del Sistema</h2>
            <p>Estimado/a,</p>
            <p>{{message}}</p>
            <p><strong>Prioridad:</strong> {{priority}}</p>
            <br>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Notificación de Finiquito Firmado',
        'template_type': 'settlement_signed',
        'recipient_type': 'user',
        'subject': 'Finiquito Firmado - {{settlement_number}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #28a745;">Finiquito Firmado</h2>
            <p>Estimado {{user_name}},</p>
            <p>El finiquito del siniestro {{claim_number}} ha sido firmado.</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Número de Finiquito:</strong> {{settlement_number}}<br>
                <strong>Monto final:</strong> ${{final_amount}}
            </div>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    },
    {
        'name': 'Notificación de Pago Completado',
        'template_type': 'payment_completed',
        'recipient_type': 'user',
        'subject': 'Pago Completado - {{settlement_number}}',
        'body_html': '''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #28a745;">Pago Completado</h2>
            <p>Estimado {{user_name}},</p>
            <p>Se ha completado el pago del finiquito del siniestro {{claim_number}}.</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Número de Finiquito:</strong> {{settlement_number}}<br>
                <strong>Monto pagado:</strong> ${{payment_amount}}<br>
                <strong>Fecha de pago:</strong> {{payment_date}}
            </div>
            <p>Atentamente,<br>Sistema de Gestión de Seguros UTPL</p>
        </div>
        '''
    }
]

for template_data in templates:
    template, created = EmailTemplate.objects.get_or_create(
        name=template_data['name'],
        defaults=template_data
    )
    if created:
        print(f'[OK] Creada plantilla: {template.name}')
    else:
        print(f'[SKIP] Ya existe: {template.name}')

print("\n[OK] Plantillas de email creadas exitosamente!")




