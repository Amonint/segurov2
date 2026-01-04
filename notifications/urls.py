from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),

    # Alerts
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/create/', views.alert_create, name='alert_create'),
    path('alerts/<int:pk>/', views.alert_detail, name='alert_detail'),
    path('alerts/<int:pk>/edit/', views.alert_edit, name='alert_edit'),
    path('alerts/<int:pk>/execute/', views.alert_execute, name='alert_execute'),
    path('alerts/<int:pk>/delete/', views.alert_delete, name='alert_delete'),
    path('alerts/run-all/', views.run_all_alerts, name='run_all_alerts'),

    # Email templates
    path('email-templates/', views.email_templates_list, name='email_templates_list'),
    path('email-templates/create/', views.email_templates_create, name='email_templates_create'),
    path('email-templates/<int:pk>/edit/', views.email_templates_edit, name='email_templates_edit'),
    path('email-templates/<int:pk>/test/', views.test_email_template, name='test_email_template'),

    # Email logs
    path('email-logs/', views.email_logs_list, name='email_logs_list'),
    path('email-logs/<int:pk>/', views.email_logs_detail, name='email_logs_detail'),
]
