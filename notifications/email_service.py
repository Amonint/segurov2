"""
Email service for simulated email sending
"""

from .models import EmailLog
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending simulated emails
    """

    @staticmethod
    def send_claim_reported_notification(claim):
        """
        Send notifications when a claim is reported
        """
        try:
            # Send to broker if exists
            if claim.policy and claim.policy.broker:
                broker_email = claim.policy.broker.email
                if broker_email:
                    success, message = EmailLog.send_email(
                        template_type='claim_reported',
                        recipient_email=broker_email,
                        recipient_name=claim.policy.broker.name,
                        context={
                            'claim_number': claim.claim_number,
                            'policy_number': claim.policy.policy_number,
                            'incident_date': claim.incident_date.strftime('%d/%m/%Y'),
                            'incident_location': claim.incident_location,
                            'incident_description': claim.incident_description,
                            'estimated_loss': f"{claim.estimated_loss:.2f}",
                            'reported_by': claim.reported_by.get_full_name(),
                            'assigned_to': claim.assigned_to.get_full_name() if claim.assigned_to else 'No asignado',
                        },
                        claim=claim,
                        policy=claim.policy
                    )
                    logger.info(f"Email to broker: {message}")

            # Send confirmation to reporter
            reporter_email = claim.reported_by.email
            if reporter_email:
                success, message = EmailLog.send_email(
                    template_type='claim_reported',
                    recipient_email=reporter_email,
                    recipient_name=claim.reported_by.get_full_name(),
                    context={
                        'user_name': claim.reported_by.get_full_name(),
                        'claim_number': claim.claim_number,
                        'policy_number': claim.policy.policy_number if claim.policy else 'Sin póliza',
                        'incident_date': claim.incident_date.strftime('%d/%m/%Y'),
                        'status': claim.get_status_display(),
                    },
                    claim=claim,
                    policy=claim.policy
                )
                logger.info(f"Email to reporter: {message}")

        except Exception as e:
            logger.error(f"Error sending claim reported notifications: {e}")

    @staticmethod
    def send_policy_expiring_notification(user, policy, days_remaining):
        """
        Send notification for expiring policy
        """
        try:
            success, message = EmailLog.send_email(
                template_type='policy_expiring',
                recipient_email=user.email,
                recipient_name=user.get_full_name(),
                context={
                    'user_name': user.get_full_name(),
                    'policy_number': policy.policy_number,
                    'insurance_company': policy.insurance_company.name,
                    'end_date': policy.end_date.strftime('%d/%m/%Y'),
                    'days_remaining': days_remaining,
                },
                policy=policy
            )
            logger.info(f"Policy expiring email: {message}")

        except Exception as e:
            logger.error(f"Error sending policy expiring notification: {e}")

    @staticmethod
    def send_payment_due_notification(user, invoice, days_remaining):
        """
        Send notification for payment due
        """
        try:
            success, message = EmailLog.send_email(
                template_type='payment_due',
                recipient_email=user.email,
                recipient_name=user.get_full_name(),
                context={
                    'user_name': user.get_full_name(),
                    'invoice_number': invoice.invoice_number,
                    'policy_number': invoice.policy.policy_number,
                    'due_date': invoice.due_date.strftime('%d/%m/%Y'),
                    'total_amount': f"{invoice.total_amount:.2f}",
                    'days_remaining': days_remaining,
                },
                invoice=invoice,
                policy=invoice.policy
            )
            logger.info(f"Payment due email: {message}")

        except Exception as e:
            logger.error(f"Error sending payment due notification: {e}")

    @staticmethod
    def send_claim_status_update(claim, old_status, new_status):
        """
        Send notification when claim status changes
        """
        try:
            # Send to assigned user
            if claim.assigned_to and claim.assigned_to.email:
                success, message = EmailLog.send_email(
                    template_type='claim_updated',
                    recipient_email=claim.assigned_to.email,
                    recipient_name=claim.assigned_to.get_full_name(),
                    context={
                        'user_name': claim.assigned_to.get_full_name(),
                        'claim_number': claim.claim_number,
                        'old_status': old_status,
                        'new_status': new_status,
                        'policy_number': claim.policy.policy_number if claim.policy else 'Sin póliza',
                    },
                    claim=claim
                )
                logger.info(f"Claim status update email: {message}")

        except Exception as e:
            logger.error(f"Error sending claim status update: {e}")

    @staticmethod
    def get_email_logs(filters=None):
        """
        Get email logs with optional filters
        """
        queryset = EmailLog.objects.select_related(
            'template', 'claim', 'policy', 'invoice', 'created_by'
        ).order_by('-created_at')

        if filters:
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            if 'template_type' in filters:
                queryset = queryset.filter(template__template_type=filters['template_type'])
            if 'date_from' in filters:
                queryset = queryset.filter(created_at__date__gte=filters['date_from'])
            if 'date_to' in filters:
                queryset = queryset.filter(created_at__date__lte=filters['date_to'])

        return queryset

    @staticmethod
    def get_email_stats():
        """
        Get email statistics
        """
        from django.db.models import Count
        return EmailLog.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
