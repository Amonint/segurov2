from decimal import Decimal
from datetime import timedelta

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
            username='reporter',
            password='testpass123',
            role='requester'
        )
        self.manager = UserProfile.objects.create_user(
            username='manager',
            password='testpass123',
            role='insurance_manager'
        )
        self.company = InsuranceCompany.objects.create(
            name='Aseguradora Test',
            ruc='1234567890123'
        )
        today = timezone.now().date()
        self.policy = Policy.objects.create(
            insurance_company=self.company,
            group_type='patrimoniales',
            subgroup='General',
            branch='Riesgos',
            start_date=today,
            end_date=today + timedelta(days=365),
            insured_value=Decimal('10000.00'),
            status='active'
        )

    def create_claim(self):
        today = timezone.now().date()
        return Claim.objects.create(
            policy=self.policy,
            incident_date=today,
            report_date=today,
            incident_location='Campus',
            incident_description='Daño por agua',
            asset_type='equipo_electronico',
            asset_description='Laptop',
            estimated_loss=Decimal('500.00'),
            reported_by=self.reporter
        )

    def test_status_change_creates_timeline(self):
        claim = self.create_claim()
        claim.change_status('documentation_pending', self.manager)

        self.assertEqual(claim.status, 'documentation_pending')
        entry = ClaimTimeline.objects.filter(
            claim=claim,
            event_type='status_change'
        ).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.old_status, 'reported')
        self.assertEqual(entry.new_status, 'documentation_pending')

    def test_invalid_status_transition_raises(self):
        claim = self.create_claim()
        with self.assertRaises(ValidationError):
            claim.change_status('paid', self.manager)
