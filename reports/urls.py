from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Reports
    path('', views.report_list, name='report_list'),
    path('policies/', views.policies_report, name='policies_report'),
    path('claims/', views.claims_report, name='claims_report'),
    path('invoices/', views.invoices_report, name='invoices_report'),
    path('financial/', views.financial_report, name='financial_report'),

    # Export reports
    path('policies/export/', views.export_policies_report, name='export_policies_report'),
    path('claims/export/', views.export_claims_report, name='export_claims_report'),
    path('financial/export/', views.export_financial_report, name='export_financial_report'),
]
