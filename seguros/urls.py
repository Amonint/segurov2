"""
URL configuration for seguros project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", lambda request: redirect('accounts:dashboard') if request.user.is_authenticated else redirect('accounts:login'), name='home'),
    path("color-palette/", TemplateView.as_view(template_name='color_palette.html'), name='color_palette'),

    # App URLs
    path("accounts/", include('accounts.urls')),
    path("policies/", include('policies.urls')),
    path("claims/", include('claims.urls')),
    path("invoices/", include('invoices.urls')),
    path("assets/", include('assets.urls')),
    path("companies/", include('companies.urls')),
    path("brokers/", include('brokers.urls')),
    path("reports/", include('reports.urls')),
    path("notifications/", include('notifications.urls')),
    path("audit/", include('audit.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
