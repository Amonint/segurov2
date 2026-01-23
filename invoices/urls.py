from django.urls import path

from . import views

app_name = "invoices"

urlpatterns = [
    # Invoice management
    path("", views.invoice_list, name="invoice_list"),
    path("create/", views.invoice_create, name="invoice_create"),
    path("<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),
    path("<int:pk>/mark-paid/", views.invoice_mark_paid, name="invoice_mark_paid"),
    path("<int:pk>/delete/", views.invoice_delete, name="invoice_delete"),
    path("<int:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("bulk-action/", views.invoice_bulk_action, name="invoice_bulk_action"),
]
