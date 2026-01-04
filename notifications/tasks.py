from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from .models import Notification, EmailLog, Alert
from policies.models import Policy
from claims.models import Claim, ClaimDocument
from invoices.models import Invoice
from assets.models import Asset
from accounts.models import UserProfile


def execute_alert(alert):
    """
    Execute an alert and create notifications
    """
    results = {
        'notifications_created': 0,
        'emails_sent': 0,
        'errors': []
    }

    try:
        if alert.alert_type == 'policy_expiring':
            results.update(execute_policy_expiring_alert(alert))
        elif alert.alert_type == 'policy_expired':
            results.update(execute_policy_expired_alert(alert))
        elif alert.alert_type == 'invoice_overdue':
            results.update(execute_invoice_overdue_alert(alert))
        elif alert.alert_type == 'claim_overdue':
            results.update(execute_claim_overdue_alert(alert))
        elif alert.alert_type == 'document_overdue':
            results.update(execute_document_overdue_alert(alert))
        elif alert.alert_type == 'payment_due':
            results.update(execute_payment_due_alert(alert))
        elif alert.alert_type == 'maintenance_required':
            results.update(execute_maintenance_required_alert(alert))
        elif alert.alert_type == 'system_alert':
            results.update(execute_system_alert(alert))

    except Exception as e:
        results['errors'].append(f"Error executing alert {alert.name}: {str(e)}")

    return results


def execute_policy_expiring_alert(alert):
    """
    Alert for policies expiring soon
    """
    results = {'notifications_created': 0, 'emails_sent': 0}

    # Get conditions
    days_ahead = alert.conditions.get('days_ahead', 30)

    # Find expiring policies
    expiry_date = timezone.now().date() + timedelta(days=days_ahead)
    expiring_policies = Policy.objects.filter(
        end_date__lte=expiry_date,
        end_date__gte=timezone.now().date(),
        status='active'
    ).select_related('responsible_user', 'insurance_company')

    for policy in expiring_policies:
        days_until_expiry = (policy.end_date - timezone.now().date()).days

        # Create notification for responsible user
        if policy.responsible_user:
            notification = Notification.create_notification(
                user=policy.responsible_user,
                notification_type='policy_expiring',
                title=f'Póliza por vencer: {policy.policy_number}',
                message=f'La póliza {policy.policy_number} de {policy.insurance_company.name} vence en {days_until_expiry} días ({policy.end_date}).',
                priority='high' if days_until_expiry <= 7 else 'medium',
                link=f'/policies/{policy.pk}/'
            )
            notification.related_object_type = 'policy'
            notification.related_object_id = policy.id
            notification.save()
            results['notifications_created'] += 1

        # Send email if configured
        email_list = alert.get_email_list()
        for email in email_list:
            success, _ = EmailLog.send_email(
                template_type='policy_expiring',
                recipient_email=email,
                context={
                    'policy_number': policy.policy_number,
                    'company_name': policy.insurance_company.name,
                    'days_until_expiry': days_until_expiry,
                    'expiry_date': policy.end_date.strftime('%d/%m/%Y'),
                    'policy_url': f'/policies/{policy.pk}/'
                },
                policy=policy
            )
            if success:
                results['emails_sent'] += 1

    return results


def execute_policy_expired_alert(alert):
    """
    Alert for expired policies
    """
    results = {'notifications_created': 0, 'emails_sent': 0}

    # Find expired policies from last 7 days
    week_ago = timezone.now().date() - timedelta(days=7)
    expired_policies = Policy.objects.filter(
        end_date__gte=week_ago,
        end_date__lt=timezone.now().date(),
        status='active'
    ).select_related('responsible_user', 'insurance_company')

    for policy in expired_policies:
        # Create notification for responsible user
        if policy.responsible_user:
            notification = Notification.create_notification(
                user=policy.responsible_user,
                notification_type='policy_expired',
                title=f'Póliza vencida: {policy.policy_number}',
                message=f'La póliza {policy.policy_number} de {policy.insurance_company.name} ha vencido el {policy.end_date}.',
                priority='urgent',
                link=f'/policies/{policy.pk}/'
            )
            notification.related_object_type = 'policy'
            notification.related_object_id = policy.id
            notification.save()
            results['notifications_created'] += 1

        # Send email if configured
        email_list = alert.get_email_list()
        for email in email_list:
            success, _ = EmailLog.send_email(
                template_type='policy_expired',
                recipient_email=email,
                context={
                    'policy_number': policy.policy_number,
                    'company_name': policy.insurance_company.name,
                    'expiry_date': policy.end_date.strftime('%d/%m/%Y'),
                    'policy_url': f'/policies/{policy.pk}/'
                },
                policy=policy
            )
            if success:
                results['emails_sent'] += 1

    return results


def execute_invoice_overdue_alert(alert):
    """
    Alert for overdue invoices
    """
    results = {'notifications_created': 0, 'emails_sent': 0}

    # Find overdue invoices
    overdue_invoices = Invoice.objects.filter(
        payment_status='pending',
        due_date__lt=timezone.now().date()
    ).select_related('created_by', 'policy__insurance_company')

    for invoice in overdue_invoices:
        days_overdue = (timezone.now().date() - invoice.due_date).days

        # Create notification for creator
        if invoice.created_by:
            notification = Notification.create_notification(
                user=invoice.created_by,
                notification_type='invoice_overdue',
                title=f'Factura vencida: {invoice.invoice_number}',
                message=f'La factura {invoice.invoice_number} por ${invoice.total_amount} está vencida hace {days_overdue} días.',
                priority='high',
                link=f'/invoices/{invoice.pk}/'
            )
            notification.related_object_type = 'invoice'
            notification.related_object_id = invoice.id
            notification.save()
            results['notifications_created'] += 1

        # Send email if configured
        email_list = alert.get_email_list()
        for email in email_list:
            success, _ = EmailLog.send_email(
                template_type='invoice_overdue',
                recipient_email=email,
                context={
                    'invoice_number': invoice.invoice_number,
                    'amount': str(invoice.total_amount),
                    'days_overdue': days_overdue,
                    'due_date': invoice.due_date.strftime('%d/%m/%Y'),
                    'invoice_url': f'/invoices/{invoice.pk}/'
                },
                invoice=invoice
            )
            if success:
                results['emails_sent'] += 1

    return results


def execute_claim_overdue_alert(alert):
    """
    Alert for overdue claims
    """
    results = {'notifications_created': 0, 'emails_sent': 0}

    # Find claims that haven't been updated in 30+ days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    overdue_claims = Claim.objects.filter(
        status__in=['reported', 'documentation_pending', 'sent_to_insurer', 'under_evaluation'],
        updated_at__lt=thirty_days_ago
    ).select_related('assigned_to', 'policy__insurance_company')

    for claim in overdue_claims:
        days_overdue = (timezone.now() - claim.updated_at).days

        # Create notification for assigned user
        if claim.assigned_to:
            notification = Notification.create_notification(
                user=claim.assigned_to,
                notification_type='claim_overdue',
                title=f'Siniestro atrasado: {claim.claim_number}',
                message=f'El siniestro {claim.claim_number} no ha sido actualizado hace {days_overdue} días.',
                priority='high',
                link=f'/claims/{claim.pk}/'
            )
            notification.related_object_type = 'claim'
            notification.related_object_id = claim.id
            notification.save()
            results['notifications_created'] += 1

        # Send email if configured
        email_list = alert.get_email_list()
        for email in email_list:
            success, _ = EmailLog.send_email(
                template_type='claim_overdue',
                recipient_email=email,
                context={
                    'claim_number': claim.claim_number,
                    'policy_number': claim.policy.policy_number,
                    'days_overdue': days_overdue,
                    'last_update': claim.updated_at.strftime('%d/%m/%Y %H:%M'),
                    'claim_url': f'/claims/{claim.pk}/'
                },
                claim=claim
            )
            if success:
                results['emails_sent'] += 1

    return results


def execute_document_overdue_alert(alert):
    """
    Alert for overdue required documents
    """
    results = {'notifications_created': 0, 'emails_sent': 0}

    # Find overdue required documents
    overdue_documents = ClaimDocument.objects.filter(
        is_required=True,
        required_deadline__lt=timezone.now().date()
    ).exclude(
        claim__status__in=['closed', 'paid', 'rejected']
    ).select_related('claim', 'uploaded_by')

    for document in overdue_documents:
        days_overdue = (timezone.now().date() - document.required_deadline).days

        # Create notification for claim assigned user
        if document.claim.assigned_to:
            notification = Notification.create_notification(
                user=document.claim.assigned_to,
                notification_type='document_overdue',
                title=f'Documento vencido: {document.document_name}',
                message=f'El documento requerido "{document.document_name}" para el siniestro {document.claim.claim_number} está vencido hace {days_overdue} días.',
                priority='urgent',
                link=f'/claims/{document.claim.pk}/documents/'
            )
            notification.related_object_type = 'claim'
            notification.related_object_id = document.claim.id
            notification.save()
            results['notifications_created'] += 1

        # Send email if configured
        email_list = alert.get_email_list()
        for email in email_list:
            success, _ = EmailLog.send_email(
                template_type='document_overdue',
                recipient_email=email,
                context={
                    'document_name': document.document_name,
                    'claim_number': document.claim.claim_number,
                    'days_overdue': days_overdue,
                    'deadline': document.required_deadline.strftime('%d/%m/%Y'),
                    'claim_url': f'/claims/{document.claim.pk}/'
                },
                claim=document.claim
            )
            if success:
                results['emails_sent'] += 1

    return results


def execute_payment_due_alert(alert):
    """
    Alert for upcoming payments
    """
    results = {'notifications_created': 0, 'emails_sent': 0}

    # Get conditions
    days_ahead = alert.conditions.get('days_ahead', 7)

    # Find upcoming payments
    due_date = timezone.now().date() + timedelta(days=days_ahead)
    upcoming_invoices = Invoice.objects.filter(
        payment_status='pending',
        due_date__lte=due_date,
        due_date__gte=timezone.now().date()
    ).select_related('created_by', 'policy__insurance_company')

    for invoice in upcoming_invoices:
        days_until_due = (invoice.due_date - timezone.now().date()).days

        # Create notification for creator
        if invoice.created_by:
            notification = Notification.create_notification(
                user=invoice.created_by,
                notification_type='payment_due',
                title=f'Pago próximo: {invoice.invoice_number}',
                message=f'La factura {invoice.invoice_number} por ${invoice.total_amount} vence en {days_until_due} días.',
                priority='medium',
                link=f'/invoices/{invoice.pk}/'
            )
            notification.related_object_type = 'invoice'
            notification.related_object_id = invoice.id
            notification.save()
            results['notifications_created'] += 1

        # Send email if configured
        email_list = alert.get_email_list()
        for email in email_list:
            success, _ = EmailLog.send_email(
                template_type='payment_due',
                recipient_email=email,
                context={
                    'invoice_number': invoice.invoice_number,
                    'amount': str(invoice.total_amount),
                    'days_until_due': days_until_due,
                    'due_date': invoice.due_date.strftime('%d/%m/%Y'),
                    'invoice_url': f'/invoices/{invoice.pk}/'
                },
                invoice=invoice
            )
            if success:
                results['emails_sent'] += 1

    return results


def execute_maintenance_required_alert(alert):
    """
    Alert for assets requiring maintenance
    """
    results = {'notifications_created': 0, 'emails_sent': 0}

    # Find assets with poor condition
    maintenance_assets = Asset.objects.filter(
        condition_status__in=['regular', 'malo'],
        is_insured=True
    ).select_related('custodian', 'responsible_user')

    for asset in maintenance_assets:
        # Create notification for custodian
        if asset.custodian:
            notification = Notification.create_notification(
                user=asset.custodian,
                notification_type='maintenance_required',
                title=f'Mantenimiento requerido: {asset.name}',
                message=f'El activo "{asset.name}" ({asset.asset_code}) requiere mantenimiento. Estado actual: {asset.get_condition_status_display()}.',
                priority='medium',
                link=f'/assets/{asset.pk}/'
            )
            notification.related_object_type = 'asset'
            notification.related_object_id = asset.id
            notification.save()
            results['notifications_created'] += 1

        # Send email if configured
        email_list = alert.get_email_list()
        for email in email_list:
            success, _ = EmailLog.send_email(
                template_type='maintenance_required',
                recipient_email=email,
                context={
                    'asset_code': asset.asset_code,
                    'asset_name': asset.name,
                    'condition': asset.get_condition_status_display(),
                    'asset_url': f'/assets/{asset.pk}/'
                }
            )
            if success:
                results['emails_sent'] += 1

    return results


def execute_system_alert(alert):
    """
    Custom system alert
    """
    results = {'notifications_created': 0, 'emails_sent': 0}

    # Get alert message from conditions
    message = alert.conditions.get('message', 'Alerta del sistema')
    priority = alert.conditions.get('priority', 'medium')

    # Create notifications for all recipients
    for user in alert.recipients.all():
        notification = Notification.create_notification(
            user=user,
            notification_type='system_alert',
            title=alert.name,
            message=message,
            priority=priority
        )
        results['notifications_created'] += 1

    # Send emails
    email_list = alert.get_email_list()
    for email in email_list:
        success, _ = EmailLog.send_email(
            template_type='system_alert',
            recipient_email=email,
            context={
                'alert_name': alert.name,
                'message': message,
                'priority': priority
            }
        )
        if success:
            results['emails_sent'] += 1

    return results


def run_scheduled_alerts():
    """
    Run all scheduled alerts that are due
    """
    alerts = Alert.objects.filter(is_active=True)

    total_results = {
        'alerts_executed': 0,
        'notifications_created': 0,
        'emails_sent': 0,
        'errors': []
    }

    for alert in alerts:
        if alert.should_run():
            results = alert.execute()
            total_results['alerts_executed'] += 1
            total_results['notifications_created'] += results.get('notifications_created', 0)
            total_results['emails_sent'] += results.get('emails_sent', 0)
            total_results['errors'].extend(results.get('errors', []))

    return total_results
