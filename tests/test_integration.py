from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from assets.models import Asset
from claims.models import Claim
from companies.models import InsuranceCompany
from policies.models import Policy


class IntegrationTests(TestCase):
    """
    Integration tests covering end-to-end workflows
    """

    def setUp(self):
        # Create users
        self.admin = UserProfile.objects.create_user(
            username="admin", password="testpass123", role="admin"
        )
        self.manager = UserProfile.objects.create_user(
            username="manager", password="testpass123", role="insurance_manager"
        )
        self.requester = UserProfile.objects.create_user(
            username="requester", password="testpass123", role="requester"
        )

        # Create company
        self.company = InsuranceCompany.objects.create(
            name="Test Insurance Company",
            ruc="1234567890123"
        )

        # Create dates
        self.today = timezone.now().date()
        self.next_year = self.today + timedelta(days=365)

    def test_complete_policy_claim_workflow(self):
        """
        Test the complete workflow from policy creation to claim processing
        """
        # 1. Create policy
        policy = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=self.next_year,
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Equipo electrónico",
            prima=Decimal("500.00"),
            responsible_user=self.manager,
        )

        # 2. Create asset
        asset = Asset.objects.create(
            asset_code="ASSET001",
            name="Laptop Test",
            asset_type="equipo_electronico",
            location="Office",
            acquisition_date=self.today,
            acquisition_cost=Decimal("1000.00"),
            current_value=Decimal("800.00"),
            custodian=self.requester,
            responsible_user=self.manager,
            is_insured=True,
            insurance_policy=policy
        )

        # 3. Create claim
        claim = Claim.objects.create(
            policy=policy,
            asset=asset,
            fecha_siniestro=self.today,
            incident_date=self.today,
            report_date=self.today,
            causa="Daño por agua",
            ubicacion_detallada="Oficina principal",
            incident_location="Oficina",
            incident_description="Daño por agua en laptop",
            estimated_loss=Decimal("500.00"),
            reportante=self.requester,
            reported_by=self.requester,
        )

        # 4. Test workflow transitions
        # Requester creates claim (starts as pendiente)
        self.assertEqual(claim.status, "pendiente")

        # Manager reviews and approves
        claim.change_status("en_revision", self.manager)
        self.assertEqual(claim.status, "en_revision")

        claim.change_status("aprobado", self.manager)
        self.assertEqual(claim.status, "aprobado")

        # Admin liquidates
        claim.change_status("liquidado", self.admin)
        self.assertEqual(claim.status, "liquidado")

        # Manager pays
        claim.change_status("pagado", self.manager)
        self.assertEqual(claim.status, "pagado")

        # Verify relationships
        self.assertEqual(policy.claims.count(), 1)
        self.assertEqual(asset.claims.count(), 1)
        self.assertEqual(claim.policy, policy)
        self.assertEqual(claim.asset, asset)

    def test_user_permissions_integration(self):
        """
        Test that user permissions work correctly across the system
        """
        # Admin should have all permissions
        self.assertTrue(self.admin.has_perm("policies.policies_create"))
        self.assertTrue(self.admin.has_perm("claims.claims_manage"))
        self.assertTrue(self.admin.has_perm("assets.assets_manage"))

        # Manager should have limited permissions
        self.assertTrue(self.manager.has_perm("policies.policies_create"))
        self.assertTrue(self.manager.has_perm("claims.claims_manage"))
        self.assertFalse(self.manager.has_perm("assets.assets_manage"))

        # Requester should have minimal permissions
        self.assertTrue(self.requester.has_perm("claims.claims_create"))
        self.assertFalse(self.requester.has_perm("policies.policies_create"))
        self.assertFalse(self.requester.has_perm("assets.assets_manage"))

    def test_policy_expiration_check(self):
        """
        Test policy expiration logic
        """
        # Create policy expiring soon
        expiring_date = self.today + timedelta(days=15)
        policy = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=self.today,
            end_date=expiring_date,
            insured_value=Decimal("10000.00"),
            objeto_asegurado="Test Object",
            prima=Decimal("500.00"),
            responsible_user=self.manager,
        )

        # Should be expiring within 30 days
        self.assertTrue(policy.is_expiring_soon(30))
        # But not within 10 days
        self.assertFalse(policy.is_expiring_soon(10))