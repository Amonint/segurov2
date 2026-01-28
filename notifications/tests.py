from django.test import TestCase

from accounts.models import UserProfile
from notifications.models import EmailTemplate, Notification


class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username="notifier", password="testpass123", role="admin"
        )
        self.recipient = UserProfile.objects.create_user(
            username="recipient", password="testpass123", role="requester"
        )

    def test_notification_creation(self):
        notification = Notification.create_notification(
            user=self.recipient,
            notification_type="alert",
            title="Test Notification",
            message="This is a test notification",
            priority="normal",
        )
        self.assertEqual(notification.user, self.recipient)
        self.assertEqual(notification.notification_type, "alert")
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.priority, "normal")
        self.assertFalse(notification.is_read)

    def test_notification_mark_as_read(self):
        notification = Notification.create_notification(
            user=self.recipient,
            notification_type="info",
            title="Test Notification",
            message="Test message",
            priority="low",
        )
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_notification_type_accepts_overdue(self):
        notification = Notification.create_notification(
            user=self.user,
            notification_type="invoice_overdue",
            title="Factura vencida",
            message="Factura vencida de prueba",
            priority="normal",
        )
        notification.full_clean()

    def test_email_template_creation(self):
        template = EmailTemplate.objects.create(
            name="Test Template",
            template_type="general",
            recipient_type="user",
            subject="Test Subject",
            body_html="<p>Test body</p>",
            created_by=self.user
        )
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.template_type, "general")
        self.assertEqual(template.subject, "Test Subject")

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

    def test_email_template_str_method(self):
        template = EmailTemplate.objects.create(
            name="Test Template",
            template_type="system_alert",
            recipient_type="user",
            subject="Test Subject",
            body_html="<p>Test body</p>",
            created_by=self.user
        )
        expected_str = "Alerta del Sistema - Test Template"
        self.assertEqual(str(template), expected_str)
