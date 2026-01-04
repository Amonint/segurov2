from django.urls import path
from . import views

app_name = 'policies'

urlpatterns = [
    # Policy management
    path('', views.policy_list, name='policy_list'),
    path('create/', views.policy_create, name='policy_create'),
    path('<int:pk>/', views.policy_detail, name='policy_detail'),
    path('<int:pk>/edit/', views.policy_edit, name='policy_edit'),
    path('<int:pk>/delete/', views.policy_delete, name='policy_delete'),

    # Policy documents
    path('<int:pk>/documents/', views.policy_documents, name='policy_documents'),
    path('<int:pk>/documents/upload/', views.policy_document_upload, name='policy_document_upload'),
    path('documents/<int:pk>/delete/', views.policy_document_delete, name='policy_document_delete'),
]
