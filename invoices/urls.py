from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    # Invoice management
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.invoice_create, name='invoice_create'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]
