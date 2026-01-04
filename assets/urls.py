from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # Asset management
    path('', views.asset_list, name='asset_list'),
    path('create/', views.asset_create, name='asset_create'),
    path('<int:pk>/', views.asset_detail, name='asset_detail'),
    path('<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('<int:pk>/delete/', views.asset_delete, name='asset_delete'),
]
