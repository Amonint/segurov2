from django.test import TestCase

from accounts.models import UserProfile
from notifications.models import EmailTemplate, Notification


class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username="notifier", password="testpass123", role="admin"
        )

    def test_notification_type_accepts_overdue(self):
        notification = Notification.create_notification(
            user=self.user,
            notification_type="invoice_overdue",
            title="Factura vencida",
            message="Factura vencida de prueba",
            priority="normal",
        )
        notification.full_clean()

    def test_email_template_type_payment_completed(self):
        template = EmailTemplate(
            name="Pago Completado Test",
            template_type="payment_completed",
            recipient_type="user",
            subject="Pago completado",
            body_html="<p>Pago completado</p>",
            created_by=self.user,
        )
        template.full_clean()
