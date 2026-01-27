from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from reports.models import Report


class ReportModelTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username="testuser",
            password="testpass123",
            role="admin"
        )

    def test_report_creation_with_valid_data(self):
        report = Report.objects.create(
            name="Test Report",
            report_type="policies_summary",
            description="A test report",
            filters={"status": "active"},
            parameters={"date_range": "last_30_days"},
            created_by=self.user
        )
        self.assertEqual(report.name, "Test Report")
        self.assertEqual(report.report_type, "policies_summary")
        self.assertEqual(report.created_by, self.user)
        self.assertFalse(report.is_scheduled)

    def test_report_creation_scheduled(self):
        report = Report.objects.create(
            name="Scheduled Report",
            report_type="claims_summary",
            is_scheduled=True,
            schedule_frequency="weekly",
            created_by=self.user
        )
        self.assertTrue(report.is_scheduled)
        self.assertEqual(report.schedule_frequency, "weekly")

    def test_report_str_method(self):
        report = Report.objects.create(
            name="Test Report",
            report_type="policies_summary",
            created_by=self.user
        )
        self.assertEqual(str(report), "Test Report")

    def test_get_report_data_structure(self):
        report = Report.objects.create(
            name="Data Report",
            report_type="policies_summary",
            filters={"status": "active"},
            created_by=self.user
        )
        data = report.get_report_data()
        self.assertIn("report_type", data)
        self.assertIn("generated_at", data)
        self.assertIn("filters", data)
        self.assertIn("data", data)
        self.assertEqual(data["report_type"], "policies_summary")
