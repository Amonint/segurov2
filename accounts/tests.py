from django.test import TestCase

from accounts.models import UserProfile


class UserProfilePermissionTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username='manager',
            password='testpass123',
            role='insurance_manager'
        )

    def test_has_perm_with_app_label(self):
        self.assertTrue(self.user.has_perm('claims.claims_write'))
        self.assertTrue(self.user.has_perm('policies.policies_read'))
        self.assertFalse(self.user.has_perm('accounts.users_manage'))

    def test_has_perms_bulk_check(self):
        self.assertTrue(self.user.has_perms(['claims.claims_read', 'claims.claims_write']))
        self.assertFalse(self.user.has_perms(['claims.claims_read', 'accounts.users_manage']))
