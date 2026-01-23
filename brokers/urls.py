from django.urls import path

from . import views

app_name = "brokers"

urlpatterns = [
    # Broker management
    path("", views.broker_list, name="broker_list"),
    path("create/", views.broker_create, name="broker_create"),
    path("<int:pk>/", views.broker_detail, name="broker_detail"),
    path("<int:pk>/edit/", views.broker_edit, name="broker_edit"),
    path("<int:pk>/delete/", views.broker_delete, name="broker_delete"),
    path(
        "<int:pk>/toggle-active/",
        views.broker_toggle_active,
        name="broker_toggle_active",
    ),
]
