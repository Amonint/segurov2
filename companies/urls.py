from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    # Insurance Companies management
    path('', views.insurance_company_list, name='insurance_company_list'),
    path('create/', views.insurance_company_create, name='insurance_company_create'),
    path('<int:pk>/', views.insurance_company_detail, name='insurance_company_detail'),
    path('<int:pk>/edit/', views.insurance_company_edit, name='insurance_company_edit'),
    path('<int:pk>/delete/', views.insurance_company_delete, name='insurance_company_delete'),
    path('<int:pk>/toggle-active/', views.insurance_company_toggle_active, name='insurance_company_toggle_active'),

    # Emission rights management
    path('emission-rights/', views.emission_rights_list, name='emission_rights_list'),
    path('emission-rights/create/', views.emission_rights_create, name='emission_rights_create'),
    path('emission-rights/<int:pk>/edit/', views.emission_rights_edit, name='emission_rights_edit'),
    path('emission-rights/<int:pk>/delete/', views.emission_rights_delete, name='emission_rights_delete'),

    # Retention types management
    path('retention-types/', views.retention_types_list, name='retention_types_list'),
    path('retention-types/create/', views.retention_types_create, name='retention_types_create'),
    path('retention-types/<int:pk>/edit/', views.retention_types_edit, name='retention_types_edit'),

    # Policy retentions management
    path('policy-retentions/', views.policy_retentions_list, name='policy_retentions_list'),
    path('policy-retentions/create/', views.policy_retentions_create, name='policy_retentions_create'),
    path('policy-retentions/<int:pk>/edit/', views.policy_retentions_edit, name='policy_retentions_edit'),
]
