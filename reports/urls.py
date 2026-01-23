from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    # Report Management
    path("", views.report_list, name="report_list"),
    path("create/", views.report_create, name="report_create"),
    path("<int:pk>/", views.report_detail, name="report_detail"),
    path("<int:pk>/edit/", views.report_edit, name="report_edit"),
    path("<int:pk>/delete/", views.report_delete, name="report_delete"),
    path("<int:pk>/execute/", views.report_execute, name="report_execute"),
    # Quick Reports
    path("quick/", views.quick_report, name="quick_report"),
    # Dashboard Reports
    path("dashboard/", views.dashboard_reports, name="dashboard_reports"),
    # Legacy Reports (keeping for compatibility)
    path("policies/", views.policies_report, name="policies_report"),
    path("claims/", views.claims_report, name="claims_report"),
    path("invoices/", views.invoices_report, name="invoices_report"),
    path("financial/", views.financial_report, name="financial_report"),
    # Legacy Export reports
    path(
        "policies/export/", views.export_policies_report, name="export_policies_report"
    ),
    path("claims/export/", views.export_claims_report, name="export_claims_report"),
    path(
        "financial/export/",
        views.export_financial_report,
        name="export_financial_report",
    ),
]
