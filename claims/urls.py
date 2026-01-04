from django.urls import path
from . import views

app_name = 'claims'

urlpatterns = [
    # Claim management
    path('', views.claim_list, name='claim_list'),
    path('create/', views.claim_create, name='claim_create'),
    path('<int:pk>/', views.claim_detail, name='claim_detail'),
    path('<int:pk>/edit/', views.claim_edit, name='claim_edit'),
    path('<int:pk>/status/', views.claim_update_status, name='claim_update_status'),

    # Claim documents
    path('<int:pk>/documents/', views.claim_documents, name='claim_documents'),
    path('<int:pk>/documents/upload/', views.claim_document_upload, name='claim_document_upload'),
    path('documents/<int:pk>/delete/', views.claim_document_delete, name='claim_document_delete'),
]
