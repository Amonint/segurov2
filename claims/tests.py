from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from claims.models import Claim, ClaimTimeline
from companies.models import InsuranceCompany
from policies.models import Policy


class ClaimWorkflowTests(TestCase):
    def setUp(self):
        self.reporter = UserProfile.objects.create_user(
            username="reporter", password="testpass123", role="requester"
        )
        self.manager = UserProfile.objects.create_user(
            username="manager", password="testpass123", role="insurance_manager"
        )
        self.admin = UserProfile.objects.create_user(
            username="admin", password="testpass123", role="admin"
        )
        self.company = InsuranceCompany.objects.create(
            name="Aseguradora Test", ruc="1234567890123"
        )
        today = timezone.now().date()
        self.policy = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=today,
            end_date=today + timedelta(days=365),
            insured_value=Decimal("10000.00"),
            status="active",
            objeto_asegurado="Equipo electrónico de oficina",
            prima=Decimal("500.00"),
            responsible_user=self.manager,
        )

    def create_claim(self):
        today = timezone.now().date()
        return Claim.objects.create(
            policy=self.policy,
            fecha_siniestro=today,
            incident_date=today,
            report_date=today,
            causa="Daño por agua en equipo electrónico",
            ubicacion_detallada="Campus universitario, edificio principal",
            incident_location="Campus",
            incident_description="Daño por agua",
            asset_type="equipo_electronico",
            asset_description="Laptop",
            estimated_loss=Decimal("500.00"),
            reportante=self.reporter,
            reported_by=self.reporter,
        )

    def test_status_change_creates_timeline(self):
        claim = self.create_claim()
        claim.change_status("en_revision", self.manager)

        self.assertEqual(claim.status, "en_revision")
        entry = ClaimTimeline.objects.filter(
            claim=claim, event_type="status_change"
        ).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.old_status, "pendiente")
        self.assertEqual(entry.new_status, "en_revision")

    def test_invalid_status_transition_raises(self):
        claim = self.create_claim()
        with self.assertRaises(ValidationError):
            claim.change_status("pagado", self.manager)  # Cannot go from pendiente to pagado

    def test_can_change_status_by_role(self):
        claim = self.create_claim()
        # Requester can only stay in pendiente
        self.assertFalse(claim.can_change_status("en_revision", self.reporter))
        # Manager can change to en_revision
        self.assertTrue(claim.can_change_status("en_revision", self.manager))
        # Admin can change to any status
        self.assertTrue(claim.can_change_status("aprobado", self.admin))

    def test_claim_validation_invalid_dates(self):
        today = timezone.now().date()
        claim = Claim(
            policy=self.policy,
            fecha_siniestro=today,
            incident_date=today,
            report_date=today - timedelta(days=1),  # Report before incident
            causa="Test cause",
            ubicacion_detallada="Test location",
            incident_location="Test",
            incident_description="Test description",
            estimated_loss=Decimal("500.00"),
            reportante=self.reporter,
            reported_by=self.reporter,
        )
        with self.assertRaises(ValidationError):
            claim.full_clean()

    def test_claim_validation_approved_amount_too_high(self):
        claim = self.create_claim()
        claim.approved_amount = Decimal("600.00")  # Higher than estimated_loss
        with self.assertRaises(ValidationError):
            claim.full_clean()

    def test_claim_validation_rejected_without_reason(self):
        claim = self.create_claim()
        claim.status = "rechazado"
        with self.assertRaises(ValidationError):
            claim.full_clean()

    def test_claim_validation_paid_without_payment_date(self):
        claim = self.create_claim()
        claim.status = "pagado"
        with self.assertRaises(ValidationError):
            claim.full_clean()

    def test_claim_str_method(self):
        claim = self.create_claim()
        expected_str = f"{claim.claim_number} - {claim.incident_description[:50]}"
        self.assertEqual(str(claim), expected_str)


class ClaimTimelineModelTests(TestCase):
    def setUp(self):
        self.reporter = UserProfile.objects.create_user(
            username="reporter", password="testpass123", role="requester"
        )
        self.manager = UserProfile.objects.create_user(
            username="manager", password="testpass123", role="insurance_manager"
        )
        self.company = InsuranceCompany.objects.create(
            name="Aseguradora Test", ruc="1234567890123"
        )
        today = timezone.now().date()
        self.policy = Policy.objects.create(
            insurance_company=self.company,
            group_type="patrimoniales",
            subgroup="General",
            branch="Riesgos",
            start_date=today,
            end_date=today + timedelta(days=365),
            insured_value=Decimal("10000.00"),
            status="active",
            objeto_asegurado="Equipo electrónico de oficina",
            prima=Decimal("500.00"),
            responsible_user=self.manager,
        )
        self.claim = Claim.objects.create(
            policy=self.policy,
            fecha_siniestro=today,
            incident_date=today,
            report_date=today,
            causa="Daño por agua en equipo electrónico",
            ubicacion_detallada="Campus universitario, edificio principal",
            incident_location="Campus",
            incident_description="Daño por agua",
            estimated_loss=Decimal("500.00"),
            reportante=self.reporter,
            reported_by=self.reporter,
            asset_type="equipo_electronico",
            asset_description="Laptop Dell",
        )

    def test_timeline_creation(self):
        timeline = ClaimTimeline.objects.create(
            claim=self.claim,
            event_type="status_change",
            event_description="Test event",
            old_status="pendiente",
            new_status="en_revision",
            created_by=self.manager,
            notes="Test notes"
        )
        self.assertEqual(timeline.claim, self.claim)
        self.assertEqual(timeline.event_type, "status_change")
        self.assertEqual(timeline.old_status, "pendiente")
        self.assertEqual(timeline.new_status, "en_revision")
