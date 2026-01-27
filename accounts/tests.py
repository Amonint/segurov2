from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import UserProfile


class UserProfilePermissionTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username="manager", password="testpass123", role="insurance_manager"
        )

    def test_has_perm_with_app_label(self):
        self.assertTrue(self.user.has_perm("claims.claims_write"))
        self.assertTrue(self.user.has_perm("policies.policies_read"))
        self.assertFalse(self.user.has_perm("accounts.users_manage"))

    def test_has_perms_bulk_check(self):
        self.assertTrue(
            self.user.has_perms(["claims.claims_read", "claims.claims_write"])
        )
        self.assertFalse(
            self.user.has_perms(["claims.claims_read", "accounts.users_manage"])
        )


class UserProfileModelTests(TestCase):
    def test_create_user_with_valid_data(self):
        user = UserProfile.objects.create_user(
            username="testuser",
            password="testpass123",
            role="requester",
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, "requester")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.get_full_name(), "Test User")

    def test_create_user_without_full_name(self):
        user = UserProfile.objects.create_user(
            username="testuser2",
            password="testpass123",
            role="admin"
        )
        self.assertEqual(user.get_full_name(), "testuser2")

    def test_role_validation_invalid_role(self):
        user = UserProfile(
            username="testuser",
            role="invalid_role"
        )
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_role_permissions_admin(self):
        user = UserProfile(role="admin")
        permissions = user.get_role_permissions()
        self.assertIn("users_manage", permissions)
        self.assertIn("claims_manage", permissions)

    def test_role_permissions_insurance_manager(self):
        user = UserProfile(role="insurance_manager")
        permissions = user.get_role_permissions()
        self.assertIn("policies_read", permissions)
        self.assertIn("claims_manage", permissions)
        self.assertNotIn("users_manage", permissions)
        self.assertNotIn("assets_manage", permissions)

    def test_role_permissions_requester(self):
        user = UserProfile(role="requester")
        permissions = user.get_role_permissions()
        self.assertIn("claims_create", permissions)
        self.assertNotIn("policies_manage", permissions)

    def test_has_perm_with_role_permissions(self):
        user = UserProfile.objects.create_user(
            username="testperm",
            password="testpass123",
            role="requester"
        )
        self.assertTrue(user.has_perm("claims.claims_create"))
        self.assertFalse(user.has_perm("policies.policies_manage"))

    def test_generate_reset_token(self):
        user = UserProfile()
        token = user.generate_reset_token()
        self.assertEqual(len(token), 32)
        self.assertTrue(token.isalnum())

    def test_soft_delete(self):
        user = UserProfile.objects.create_user(
            username="deletetest",
            password="testpass123",
            role="requester"
        )
        self.assertTrue(user.is_active)
        user.soft_delete()
        self.assertFalse(user.is_active)
