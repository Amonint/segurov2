from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from audit.models import AuditLog


class AuditLogModelTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username="testuser",
            password="testpass123",
            role="admin"
        )

    def test_audit_log_creation(self):
        audit_log = AuditLog.objects.create(
            user=self.user,
            action_type="create",
            entity_type="policy",
            entity_id="POL001",
            description="Created new policy",
            old_values=None,
            new_values={"policy_number": "POL001", "status": "active"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Test Browser)"
        )
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action_type, "create")
        self.assertEqual(audit_log.entity_type, "policy")
        self.assertEqual(audit_log.entity_id, "POL001")
        self.assertEqual(audit_log.description, "Created new policy")
        self.assertIsNotNone(audit_log.created_at)

    def test_audit_log_without_user(self):
        audit_log = AuditLog.objects.create(
            action_type="login",
            entity_type="user",
            entity_id="anonymous",
            description="Anonymous login attempt",
            ip_address="192.168.1.1"
        )
        self.assertIsNone(audit_log.user)
        self.assertEqual(audit_log.action_type, "login")

    def test_audit_log_with_changes(self):
        old_values = {"status": "pending"}
        new_values = {"status": "approved"}
        audit_log = AuditLog.objects.create(
            user=self.user,
            action_type="update",
            entity_type="claim",
            entity_id="CLAIM001",
            description="Updated claim status",
            old_values=old_values,
            new_values=new_values
        )
        self.assertEqual(audit_log.old_values, old_values)
        self.assertEqual(audit_log.new_values, new_values)

    def test_audit_log_str_method(self):
        audit_log = AuditLog.objects.create(
            user=self.user,
            action_type="create",
            entity_type="policy",
            entity_id="POL001",
            description="Created policy"
        )
        expected_str = f"{self.user.get_full_name()} - create - policy ({audit_log.created_at})"
        self.assertEqual(str(audit_log), expected_str)
