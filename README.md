# 🛡️ Sistema de Gestión de Seguros - UTPL

**Sistema integral de gestión de pólizas de seguros, siniestros, facturación y reportes**  
*Para la Universidad Técnica Particular de Loja (UTPL)*

[![Django](https://img.shields.io/badge/Django-5.1.7-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Tabla de Contenidos
- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Funcionalidades](#funcionalidades)
- [Instalación](#instalación-rápida)
- [Uso](#uso)
- [API REST](#api-rest)
- [Datos de Prueba](#datos-de-prueba)
- [Despliegue](#despliegue)
- [Contribución](#contribución)

## 📋 Descripción General

**SEGUROS v1.0** es una **aplicación web empresarial** diseñada para gestionar integralmente todas las operaciones relacionadas con seguros universitarios. Implementa una arquitectura **Modelo-Vista-Controlador (MVC)** robusta con Django, proporcionando un sistema modular, escalable y seguro.

### ¿Qué hace este sistema?

Automatiza procesos complejos de seguros incluyendo:

| Función | Descripción |
|---------|-------------|
| 🎯 **Gestión de Pólizas** | CRUD completo, numeración automática, vencimientos |
| 📋 **Siniestros** | Workflow completo (7 estados), timeline de eventos, documentos |
| 💰 **Facturación** | Cálculos automáticos de primas, IVA (15%), descuentos, retenciones |
| 📦 **Control de Bienes** | Inventario de activos, custodia, depreciación automática |
| 👥 **Gestión de Usuarios** | 3 roles con permisos granulares y autenticación segura |
| 📊 **Auditoría Integral** | Registro automático de todas las operaciones con antes/después |
| 🔔 **Notificaciones** | Sistema de alertas automáticas por email |
| 📈 **Reportes** | Generación de reportes con exportación (en desarrollo) |
| 🔐 **Seguridad** | Validación CSRF, autenticación Django, control de sesiones |

## 🏗️ Arquitectura del Proyecto

### **Patrón Arquitectónico: MVC de 3 Capas**

```
┌──────────────────────────────────────────────────────┐
│    CAPA 1: PRESENTACIÓN (Views + Templates)          │
│  • Templates HTML (Django Templates)                 │
│  • Vistas (Views) - Controladores                    │
│  • Formularios validados (Django Forms)              │
│  • Bootstrap 5 + Crispy Forms                        │
├──────────────────────────────────────────────────────┤
│  CAPA 2: LÓGICA DE NEGOCIO (Modelos Django)         │
│  • Modelos de datos con validaciones                 │
│  • Métodos de lógica de negocio                      │
│  • Cálculos automáticos                              │
│  • Generación de números únicos                      │
│  • Validaciones complejas                            │
├──────────────────────────────────────────────────────┤
│   CAPA 3: ACCESO A DATOS (Persistencia)             │
│  • ORM Django (consultas seguras)                    │
│  • PostgreSQL / SQLite                               │
│  🛠️ Tecnologías

### **Backend**
| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Django** | 5.1.7 | Framework web principal |
| **Python** | 3.9+ | Lenguaje de programación |
| **PostgreSQL** | 13+ | Base de datos (producción) |
| **SQLite** | 3.x | Base de datos (desarrollo) |
| **Django ORM** | - | Consultas y validaciones |
| **Django REST Framework** | 3.16.1 | API REST |

### **Frontend**
| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Bootstrap** | 5.x | Framework CSS responsivo |
| **Crispy Forms** | 2.5 | Renderizado de formularios |
| **HTML5** | - | Estructura |
| **CSS3** | - | Estilos |
| **JavaScript** | ES6+ | Interactividad |

### **Dependencias Principales**

```txt
Django==5.1.7                    # Framework web
psycopg2-binary==2.9.11         # Adaptador PostgreSQL
python-decouple==3.8            # Variables de entorno
djangorestframework==3.16.1     # API REST
django-crispy-forms==2.5        # Formularios
crispy-bootstrap5==2025.6       # Integración Bootstrap
Pillow==11.1.0                  # Procesamiento de imágenes
```

### **Herramientas de Desarrollo (Opcionales)**

```txt
gunicorn==21.2.0               # Servidor WSGI producción
whitenoise==6.6.0              # Servir archivos estáticos
coverage==7.4.0                # Tests y cobertura
black==23.12.1                 # Formateador código
flake8==7.0.0                  # Linter
```

---

### 🎯 **¿Por qué este sistema es MVC?**

Este proyecto implementa el patrón de arquitectura **Modelo-Vista-Controlador (MVC)** de manera nativa en Django
```

### **Estructura de Aplicaciones Django**

```
segurov2/
│
├── 📁 seguros/                     # Configuración principal
│   ├── settings.py                 # Variables y configuración Django
│   ├── urls.py                     # Rutas principales
│   ├── wsgi.py                     # WSGI para producción
│   └── asgi.py                     # ASGI para async
│
├── 📁 accounts/                    # Autenticación y usuarios
│   ├── models.py                   # UserProfile (extiende Django User)
│   ├── views.py                    # Login, registro, perfil
│   ├── forms.py                    # Formularios de usuario
│   └── decorators.py               # @login_required personalizado
│
├── 📁 policies/                    # Gestión de pólizas
│   ├── models.py                   # Modelo Policy (póliza maestra)
│   ├── views.py                    # CRUD de pólizas
│   ├── forms.py                    # Validación de pólizas
│   └── admin.py                    # Administración en Django Admin
│
├── 📁 claims/                      # Gestión de siniestros
│   ├── models.py                   # Claim (siniestro) + ClaimTimeline
│   ├── views.py                    # Workflow de siniestros
│   └── forms.py                    # Formularios de estados
│
├── 📁 invoices/                    # Facturación automática
│   ├── models.py                   # Invoice (factura con cálculos)
│   ├── views.py                    # Listado y detalle de facturas
│   └── helpers.py                  # Cálculos de IVA y descuentos
│
├── 📁 assets/                      # Gestión de bienes
│   ├── models.py                   # Asset (bien/activo)
│   └── views.py                    # Inventario de bienes
│
├── 📁 companies/                   # Compañías aseguradoras
│   └── models.py                   # InsuranceCompany
│
├── 📁 brokers/                     # Corredores de seguros
│   └── models.py                   # Broker
│
├── 📁 notifications/               # Sistema de notificaciones
│   ├── models.py                   # Notification
│   ├── email_service.py            # Integración con email
│   └── tasks.py                    # Celery tasks (async)
│
├── 📁 audit/                       # Auditoría integral
│   ├── models.py                   # AuditLog (GenericForeignKey)
│   ├── middleware.py               # Captura de operaciones
│   └── views.py                    # Reportes de auditoría
│
├── 📁 reports/                     # Reportes y exportación
│   ├── models.py                   # ReportTemplate
│   └── views.py                    # Generación de reportes
│
├── 📁 templates/                   # Templates HTML
│   ├── base.html                   # Estructura base
│   ├── accounts/                   # Templates de auth
│   ├── policies/                   # Templates de pólizas
│   � Funcionalidades

### 🎯 **Gestión de Pólizas**
```
✅ Creación automática de números únicos
✅ Validaciones de fechas (inicio < fin < vencimiento)
✅ Cálculo automático de primas
✅ Gestión de documentos adjuntos
✅ Alertas de vencimiento (30 días antes)
✅ Renovación automática de pólizas
✅ Historial de cambios auditado
```

**Modelo Relacional:**
```
Policy (póliza)
├── policy_number: Único automático (POL-2025-001)
├── insurance_company: FK a CompañíaAseguradora
├── broker: FK a Corredor
├── status: [activa, vencida, cancelada, renovada]
├── group_type: [patrimoniales, personas]
└── Relaciones inversas: claims (siniestros), invoices (facturas)
```

### 💰 **Facturación Automática**
```
Proceso automático que calcula:
1. Prima base (definida en póliza)
2. IVA 15% (sobre prima)
3. Contribución Superintendencia 3.5%
4. Contribución Seguro Campesino 0.5%
5. Derechos de emisión (variable)
6. Descuentos pronto pago (hasta 5%)
7. Retenciones (configurables por usuario)
─────────────────────────────────
= TOTAL A PAGAR (automático)
```

**Estados de Pago:**
```
Pendiente → Pagada → Vencida (con fecha)
   ↓
Cancelada (reembolso)
```

### 📋 **Gestión de Siniestros (Workflow Completo)**

```
ESTADO: Pendiente de Validación
├─ Usuario reporta siniestro
├─ Adjunta documentos (fotos, reportes)
└─ Sistema valida formato

                    ↓ (Validado)

ESTADO: En Revisión
├─ Gerente analiza documentos
├─ Evalúa cobertura de póliza
└─ Calcula monto estimado

        ↓ (Aprobado) o ↓ (Cambios)

ESTADO: Aprobado O Requiere Cambios
├─ Si APROBADO → Cálculo de liquidación
└─ Si CAMBIOS → Usuario reenvía docs

                    ↓

ESTADO: Liquidado
├─ Monto final establecido
├─ Generación de comprobante
└─ Pago programado

                    ↓

ESTADO: Pagado
├─ Transferencia completada
├─ Documentación final
└─ Cierre de siniestro

O RECHAZADO (en cualquier punto)
```

**Timeline Automático:**
- Cada cambio de estado registra: usuario, fecha/hora, IP, navegador
- Permite trazar exactamente quién hizo qué y cuándo

### 📦 **Control de Bienes**
```
✅ Inventario completo de activos
✅ Asignación a custodios
✅ Depreciación automática (configurable)
✅ Relación directa con siniestros
✅ Historial de movimientos
```

**Tipos de Bienes:**
- Equipos electrónicos (laptops, servidores)
- Vehículos (carros, motos)
- Inmuebles (oficinas, almacenes)
- Maquinaria
- Acervo bibliográfico

### 🔐 **Sistema de Permisos y Roles**

```
┌─────────────────────────────────────────────────────┐
│ ADMIN (Administrador)                               │
├─────────────────────────────────────────────────────┤
│ • Acceso completo a todo el sistema                 │
│ • Gestión de usuarios y roles                       │
│ • Configuración de parámetros financieros           │
│ • Acceso a Django Admin                             │
│ • Panel de auditoría completo                       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ GERENTE DE SEGUROS (insurance_manager)              │
├─────────────────────────────────────────────────────┤
│ • CRUD completo de pólizas                          │
│ • CRUD completo de siniestros                       │
│ • Aprobación de siniestros                          │
│ • Revisión de documentos                            │
│ • Generación de reportes básicos                    │
│ • NO puede: borrar pólizas, acceder a financiero   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ CUSTODIO DE BIENES (requester)                      │
├─────────────────────────────────────────────────────┤
│ • Ver inventario de sus bienes                      │
│ • Reportar siniestros                               │
│ • Subir documentos                                  │
│ • NO puede: editar pólizas, aprobar siniestros     │
└─────────────────────────────────────────────────────┘
```

### 🔍 **Auditoría Integral**
```
CADA OPERACIÓN registra automáticamente:
├─ Tipo de acción (crear, editar, eliminar)
├─ Usuario que realizó la acción
├─ Entidad afectada (Policy, Claim, Invoice)
├─ Hora y fecha exacta
├─ IP del usuario
├─ Navegador utilizado
├─ Cambios realizados (antes y después)
└─ Estado de la transacción (exitosa/fallida)

Ejemplos de auditoría:
✓ Admin creó usuario "gerente_seguros"
✓ Custodio reportó siniestro #CLM-2025-001
✓ Gerente aprobó siniestro (monto: $500 → $750)
✓ Sistema canceló póliza vencida #POL-2024-050
```

### 🔔 **Notificaciones Automáticas**
```
El sistema envía emails automáticos para:
├─ Vencimiento próximo de póliza (30 días)
├─ Nuevo siniestro reportado
├─ Cambio de estado en siniestro
├─ Factura generada
├─ Pago de siniestro completado
└─ Alertas de seguridad (login fallido, acceso denegado)
```

---

## 🚀 Instalación Rápida                 # Templates de siniestros
│   └── ...
│
├── 📁 static/                      # Archivos estáticos
│   ├── css/                        # Estilos personalizados
│   ├── js/                         # JavaScript
│   └── img/                        # Imágenes
│
├── 📁 media/                       # Archivos subidos por usuarios
│   ├── documents/                  # PDFs, imágenes de siniestros
│   └── certificates/               # Documentos de pólizas
│
├── requirements.txt                # Dependencias Python
├── manage.py                       # Herramienta CLI Django
└── db.sqlite3                      # BD SQLite (desarrollo)
```

### 🎯 **¿Por qué este sistema es MVC?**

Este proyecto implementa el patrón de arquitectura **Modelo-Vista-Controlador (MVC)** a través del framework Django, que sigue esta arquitectura de manera nativa:

#### **🏛️ Modelo (Model) - Capa de Datos**

Los **Modelos** representan la estructura de datos y la lógica de negocio. Ejemplo:

```python
# Modelo de Usuario (accounts/models.py)
class UserProfile(AbstractUser):
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Administrador'),
        ('insurance_manager', 'Gerente'),
        ('requester', 'Custodio'),
    ])
    
    def has_view_permission(self, obj):
        """Lógica de negocio: permisos por rol"""
        if self.role == 'admin':
            return True
        return self.id == obj.owner_id

# Modelo de Póliza (policies/models.py)
class Policy(models.Model):
    policy_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    def save(self, *args, **kwargs):
        """Lógica: generación automática de número único"""
        if not self.policy_number:
            self.policy_number = self.generate_policy_number()
        super().save(*args, **kwargs)
```

#### **👁️ Vista (View) - Capa de Presentación y Control**

Las **Vistas** manejan la lógica de presentación y coordinan modelos con templates:

```python
# Vista de Controlador (claims/views.py)
@login_required
def claim_detail(request, pk):
    """Controlador: obtiene datos, aplica lógica, pasa a template"""
    claim = get_object_or_404(Claim, pk=pk)
    
    # Lógica de control
    if not request.user.can_view_claim(claim):
        raise PermissionDenied()
    
    timeline = claim.timeline.all().order_by('-created_at')
    
    # Pasa contexto al template
    return render(request, 'claims/claim_detail.html', {
        'claim': claim,
        'timeline': timeline,
        'can_approve': request.user.role == 'insurance_manager'
    })
```

#### **🎯 Enrutamiento (URLs) - Controlador de Rutas**

Las URLs en Django actúan como el controlador que direcciona las peticiones:

```python
# claims/urls.py
urlpatterns = [
    path('', views.claim_list, name='claim_list'),
    path('<int:pk>/', views.claim_detail, name='claim_detail'),
    path('create/', views.claim_create, name='claim_create'),
    path('<int:pk>/approve/', views.claim_approve, name='claim_approve'),
]
```

#### **💾 Templates (HTML) - Vista de Presentación**

Los templates renderean los datos en HTML para el usuario:

```html
<!-- templates/claims/claim_detail.html -->
{% extends 'base.html' %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h1>{{ claim.claim_number }}</h1>
        <span class="badge badge-{{ claim.status }}">{{ claim.get_status_display }}</span>
    </div>
    <div class="card-body">
        <!-- Presentación de datos -->
        {% if can_approve %}
            <button class="btn btn-success" onclick="approveClaim()">Aprobar</button>
        {% endif %}
    </div>
</div>
{% endblock %}
```

#### **🔄 Flujo Completo MVC**

```
Usuario Ingresa URL
    ↓
URL Router (urls.py) busca ruta coincidente
    ↓
Vista (view) se ejecuta
    ↓
  ├─→ Obtiene datos del Modelo
  ├─→ Aplica lógica de negocio
  └─→ Valida permisos
    ↓
Template recibe contexto
    ↓
Template renderea HTML con datos
    ↓
Navegador recibe HTML
    ↓
Usuario ve la página ✅
```

---

## 🔐 Seguridad y Validaciones

### Protecciones Implementadas
```
✅ CSRF Token en todos los formularios
✅ SQL Injection: ORM Django previene
✅ XSS: Escapado automático en templates
✅ Autenticación requerida en vistas críticas
✅ Validación de permisos por rol
✅ Rate limiting (opcional con middleware)
✅ HTTPS listo (con DEBUG=False)
✅ Contraseñas hasheadas con PBKDF2
✅ Sesiones seguras (timeout 1 hora)
✅ Auditoría de todas las operaciones
```

---

## 🚀 Instalación Rápida

### Prerrequisitos

- **Python 3.9+**
- **PostgreSQL 13+** (o SQLite para desarrollo)
- **Git**

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd segurov2
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # En Linux/Mac
# o
venv\Scripts\activate     # En Windows
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

Si no existe el archivo `requirements.txt`, instala manualmente:

```bash
pip install django psycopg2-binary python-decouple djangorestframework django-crispy-forms crispy-bootstrap5 pillow
```

### 4. Configurar Base de Datos

#### Opción A: PostgreSQL (Recomendado para producción)

```bash
# Crear base de datos en PostgreSQL
createdb seguros_db

# Crear usuario
createuser seguros_user -P
# Ingresa la contraseña: seguros_pass

# Otorgar permisos
psql -c "GRANT ALL PRIVILEGES ON DATABASE seguros_db TO seguros_user;"
```

#### Opción B: SQLite (Para desarrollo rápido)

El proyecto está configurado para usar SQLite por defecto si no hay configuración de PostgreSQL.

### 5. Configurar Variables de Entorno

Crea el archivo `.env` en la raíz del proyecto:

```bash
# Django Settings
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=seguros_db
DB_USER=seguros_user
DB_PASSWORD=seguros_pass
DB_HOST=localhost
DB_PORT=5432

# Email (opcional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_password
```

### 6. Ejecutar Migraciones

```bash
# Crear y aplicar migraciones
python manage.py makemigrations
python manage.py migrate
```

### 7. Crear Superusuario

```bash
python manage.py createsuperuser
```

O crear uno automáticamente:

```bash
python manage.py shell -c "from accounts.models import UserProfile; UserProfile.objects.create_superuser('admin', 'admin@utpl.edu.ec', 'admin123', role='admin', full_name='Administrador del Sistema')"
```

### 8. Recopilar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 9. Ejecutar el Servidor

```bash
python manage.py runserver
```

El servidor estará disponible en: http://localhost:8000

## 🔐 Credenciales de Acceso

### Usuario Administrador (creado automáticamente)
- **Usuario**: `admin`
- **Contraseña**: `admin123`
- **Rol**: Administrador

### URLs de Acceso
- **Sistema Principal**: http://localhost:8000
- **Panel de Administración**: http://localhost:8000/admin/

## 👥 Roles del Sistema

1. **Administrador**: Acceso completo a todas las funciones
2. **Gerente de Seguros**: Gestión de pólizas y siniestros
3. **Analista Financiero**: Gestión financiera y reportes
4. **Consultor**: Apoyo en siniestros y consultas
5. **Custodio de Bienes**: Gestión de bienes asignados

## 🎮 Uso del Sistema

### Acceso Inicial

```bash
# 1. Activar entorno virtual
venv\Scripts\activate  # Windows

# 2. Ejecutar servidor
python manage.py runserver

# 3. Acceder en navegador
http://localhost:8000
```

### Credenciales de Prueba

| Usuario | Contraseña | Rol | Permisos |
|---------|-----------|-----|----------|
| `admin` | `admin123` | Admin | Total |
| `gerente_seguros` | `password123` | Gerente | Pólizas + Siniestros |
| `custodio1` | `password123` | Custodio | Ver sus bienes, reportar siniestros |

### Panel de Administración

Accede a: `http://localhost:8000/admin/`
- Usuario: `admin`
- Contraseña: `admin123`

---

## 🔌 API REST

El sistema incluye endpoints REST para integración con aplicaciones externas:

```bash
# Obtener todas las pólizas
GET /api/policies/

# Obtener detalle de póliza
GET /api/policies/{id}/

# Crear póliza
POST /api/policies/
Content-Type: application/json
{
    "policy_number": "POL-2025-001",
    "insurance_company": 1,
    "premium": "5000.00",
    "start_date": "2025-01-22",
    "end_date": "2026-01-22"
}

# Obtener siniestros
GET /api/claims/?status=pendiente

# Actualizar estado de siniestro
PATCH /api/claims/{id}/
{
    "status": "en_revision"
}
```

**Documentación interactiva:**
```
http://localhost:8000/api/schema/
```

---

## 🛠️ Comandos Útiles

### Desarrollo
```bash
# Iniciar servidor (auto-reload)
python manage.py runserver

# Iniciar en puerto específico
python manage.py runserver 8000

# Shell Python interactivo con Django
python manage.py shell

# Crear nueva aplicación Django
python manage.py startapp nombreapp
```

### Migraciones y Base de Datos
```bash
# Crear migraciones basadas en cambios de modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Mostrar estado de migraciones
python manage.py showmigrations

# Crear superusuario interactivamente
python manage.py createsuperuser

# Backup completo (PostgreSQL)
pg_dump seguros_db > backup_$(date +%Y%m%d).sql

# Restaurar base de datos
psql seguros_db < backup_20250122.sql
```

### Datos y Población
```bash
# Ejecutar script de población de datos
python create_remaining_data.py

# Ejecutar seed de datos
python seed_output.txt

# Verificar integridad de datos
python verify_login_users.py
```

### Archivos Estáticos
```bash
# Recopilar archivos estáticos para producción
python manage.py collectstatic --noinput

# Limpiar archivos estáticos antiguos
python manage.py collectstatic --clear

# Verificar archivos estáticos
python manage.py findstatic logo.png
```

### Testing
```bash
# Ejecutar todos los tests
python manage.py test

# Tests de una aplicación específica
python manage.py test accounts

# Tests con cobertura
coverage run --source='.' manage.py test
coverage report

# Tests verbosos
python manage.py test --verbosity=2
```

### Verificación de Configuración
```bash
# Verificar configuración de desarrollo
python manage.py check

# Verificar configuración de producción
python manage.py check --deploy

# Ver todas las URLs del proyecto
python manage.py show_urls

# Inspeccionar modelo específico
python manage.py inspectdb
```

### Producción
```bash
# Generar requirements.txt actualizado
pip freeze > requirements.txt

# Iniciar con Gunicorn
gunicorn seguros.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Compilar archivos estáticos
python manage.py collectstatic --noinput

# Ejecutar migraciones en producción
python manage.py migrate
```

---

## 📊 Diagramas de Base de Datos

### Relaciones Principales

```
┌──────────────────┐
│ InsuranceCompany │
└────────┬─────────┘
         │ 1:N
         ▼
    ┌─────────────────┐         ┌──────────────┐
    │     Policy      │◄────────┤  Broker      │
    │   (Póliza)      │  1:N    └──────────────┘
    └────────┬────────┘
      1      │   1:N
      │      ▼
      │    ┌──────────────┐
      │    │   Invoice    │
      │    │ (Factura)    │
      │    └──────────────┘
      │
      └──────────┐
                 │ 1:N
                 ▼
            ┌──────────────┐       ┌──────────────┐
            │    Claim     │──────→│    Asset     │
            │  (Siniestro) │ 1:1   │   (Bien)     │
            └──────────────┘       └──────────────┘
                    │
                    │ 1:N
                    ▼
            ┌──────────────────┐
            │  ClaimTimeline   │
            │  (Historial)     │
            └──────────────────┘
```

### Tabla Audit (GenericForeignKey)

```
AuditLog
├─ user: FK → UserProfile
├─ action_type: ['create', 'update', 'delete', 'login', 'export']
├─ entity_type: ['policy', 'claim', 'invoice', 'asset']
├─ entity_id: ID del objeto auditado
├─ timestamp: Fecha y hora
├─ ip_address: IP del usuario
├─ user_agent: Navegador
├─ old_values: JSON con valores anteriores
└─ new_values: JSON con valores nuevos
```

---

## 📁 Estructura de Archivos

```
segurov2/
│
├── 🔧 Configuración
│   ├── .env                    # Variables de entorno (NO commitear)
│   ├── .env.example            # Template de .env
│   ├── .gitignore              # Archivos a ignorar en Git
│   ├── requirements.txt        # Dependencias Python
│   ├── Procfile               # Configuración para Heroku
│   ├── runtime.txt            # Versión Python para Heroku
│   └── README.md              # Este archivo
│
├── 📁 seguros/                # Proyecto Django principal
│   ├── settings.py            # Configuración
│   ├── urls.py                # Rutas principales
│   ├── wsgi.py                # WSGI (producción)
│   └── asgi.py                # ASGI (async)
│
├── 📱 apps/ (Aplicaciones Django)
│   │
│   ├── accounts/              # Gestión de usuarios
│   │   ├── models.py          # UserProfile
│   │   ├── views.py           # Login, logout, perfil
│   │   ├── forms.py           # Formularios
│   │   ├── decorators.py      # Validadores personalizados
│   │   └── urls.py
│   │
│   ├── policies/              # Gestión de pólizas
│   │   ├── models.py          # Policy, PolicyDocument
│   │   ├── views.py           # CRUD de pólizas
│   │   ├── forms.py           # PolicyForm, validaciones
│   │   ├── admin.py           # Admin Django
│   │   └── urls.py
│   │
│   ├── claims/                # Gestión de siniestros
│   │   ├── models.py          # Claim, ClaimTimeline, ClaimDocument
│   │   ├── views.py           # Workflow de siniestros
│   │   ├── forms.py           # Cambio de estado
│   │   └── urls.py
│   │
│   ├── invoices/              # Facturación automática
│   │   ├── models.py          # Invoice (con cálculos)
│   │   ├── views.py           # Listado de facturas
│   │   ├── helpers.py         # Funciones de cálculo
│   │   └── urls.py
│   │
│   ├── assets/                # Gestión de bienes
│   │   ├── models.py          # Asset
│   │   ├── views.py           # Inventario
│   │   └── urls.py
│   │
│   ├── companies/             # Compañías aseguradoras
│   │   ├── models.py          # InsuranceCompany, EmissionRights
│   │   └── views.py
│   │
│   ├── brokers/               # Corredores
│   │   ├── models.py          # Broker
│   │   └── views.py
│   │
│   ├── notifications/         # Sistema de notificaciones
│   │   ├── models.py          # Notification
│   │   ├── email_service.py   # Envío de emails
│   │   ├── tasks.py           # Tareas Celery
│   │   └── views.py
│   │
│   ├── audit/                 # Auditoría
│   │   ├── models.py          # AuditLog
│   │   ├── middleware.py      # Captura automática
│   │   └── views.py           # Reportes
│   │
│   └── reports/               # Reportes
│       ├── models.py          # ReportTemplate
│       └── views.py           # Generación
│
├── 📁 templates/              # Templates HTML
│   ├── base.html              # Layout base
│   ├── navbar.html            # Navegación
│   ├── accounts/              # Auth templates
│   ├── policies/              # Pólizas templates
│   ├── claims/                # Siniestros templates
│   └── ...
│
├── 📁 static/                 # Archivos estáticos
│   ├── css/
│   │   └── style.css          # Estilos personalizados
│   ├── js/
│   │   └── main.js            # JavaScript personalizado
│   └── img/                   # Logos, iconos
│
├── 📁 media/                  # Archivos subidos
│   ├── documents/             # Documentos de pólizas
│   └── claims/                # Evidencia de siniestros
│
├── 📁 staticfiles/            # Archivos recolectados (producción)
│
└── manage.py                  # CLI Django
```

---

## 🔧 Configuración Avanzada

### Configurar Email en Gmail

```
# En .env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password  # Generar en myaccount.google.com/apppasswords
```

### Usar PostgreSQL en Producción

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='seguros_db'),
        'USER': config('DB_USER', default='seguros_user'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

### Configurar Redis para Cache

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/',
    }
}
```

---

## 📈 Datos de Prueba

El sistema viene precargado con:
- **7 usuarios** con diferentes roles
- **5 compañías** aseguradoras
- **3 corredores** de seguros
- **5 pólizas** activas
- **8+ siniestros** en diferentes estados
- **5 facturas** con cálculos complejos
- **Bienes** de muestra en inventario

**Carga de datos:**
```bash
python create_remaining_data.py
```

---

## 🚀 Despliegue

### Opción 1: ngrok (Exposición Local Rápida)
```bash
# Terminal 1: Ejecutar Django
python manage.py runserver

# Terminal 2: Exponer con ngrok
ngrok http 8000
# Obtendrás URL pública: https://abc123.ngrok.io
```

### Opción 2: Heroku
```bash
# Instalar Heroku CLI
heroku login
heroku create seguros-app

# Deploy
git push heroku main

# Migraciones
heroku run python manage.py migrate

# Crear superuser
heroku run python manage.py createsuperuser
```

### Opción 3: Docker
```bash
# Construir imagen
docker build -t seguros:latest .

# Ejecutar contenedor
docker run -p 8000:8000 seguros:latest

# Con docker-compose
docker-compose up
```

Ver [guía completa de despliegue](##despliegue-completo) arriba.

---

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama de feature: `git checkout -b feature/MiFeature`
3. Commit cambios: `git commit -m 'Add MiFeature'`
4. Push: `git push origin feature/MiFeature`
5. Abrir Pull Request

### Guías de Estilo
- Usar Black para formatear código
- Seguir PEP 8
- Añadir docstrings a funciones
- Crear tests para nuevas features

---

## 📞 Soporte y Contacto

- **Email**: soporte@utpl.edu.ec
- **Issues**: Reportar en GitHub
- **Wiki**: [Documentación interna]

---

## 📝 Changelog

### v1.0.0 (Enero 2025) - Actual
✅ Implementación completa de arquitectura MVC
✅ Sistema de usuarios y roles
✅ CRUD completo de pólizas
✅ Workflow de siniestros
✅ Facturación automática
✅ Auditoría integral
✅ API REST básica
✅ Interface moderna Bootstrap 5

### Próximas versiones
🔄 Reportes avanzados con exportación PDF/Excel
🔄 Integración con Celery para tareas async
🔄 Dashboard con gráficos (Chart.js)
🔄 Notificaciones en tiempo real (WebSockets)
🔄 Integración con sistemas externos

---

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 🙏 Créditos

Desarrollado para la **Universidad Técnica Particular de Loja (UTPL)**

**Tech Stack:** Django + PostgreSQL + Bootstrap 5 + Django REST Framework

---

<div align="center">

**Made with ❤️ for UTPL**

**[↑ Volver al inicio](#-sistema-de-gestión-de-seguros---utpl)**

</div>


### Desarrollo
```bash
# Ejecutar servidor de desarrollo
python manage.py runserver

# Ejecutar servidor en puerto específico
python manage.py runserver 8000

# Ejecutar con recarga automática
python manage.py runserver --noreload

# Crear nueva app
python manage.py startapp nueva_app
```

### Base de Datos
```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Backup de base de datos (PostgreSQL)
pg_dump seguros_db > backup.sql

# Restaurar base de datos
psql seguros_db < backup.sql
```

### Archivos Estáticos
```bash
# Recopilar archivos estáticos
python manage.py collectstatic

# Limpiar archivos estáticos
python manage.py collectstatic --clear
```

### Testing
```bash
# Ejecutar todos los tests
python manage.py test

# Ejecutar tests de una app específica
python manage.py test accounts

# Ejecutar con cobertura
coverage run manage.py test
coverage report
```

### Producción
```bash
# Verificar configuración de producción
python manage.py check --deploy

# Crear archivo de requerimientos
pip freeze > requirements.txt

# Ejecutar con Gunicorn
gunicorn seguros.wsgi:application --bind 0.0.0.0:8000
```

## 📁 Estructura de Archivos

```
segurov2/
├── .env                    # Variables de entorno
├── README.md              # Este archivo
├── requirements.txt       # Dependencias Python
├── manage.py              # Comando Django
├── seguros/               # Configuración principal
│   ├── __init__.py
│   ├── settings.py        # Configuración Django
│   ├── urls.py           # URLs principales
│   ├── wsgi.py           # WSGI para producción
│   └── asgi.py           # ASGI para async
├── apps/                  # Aplicaciones Django
│   ├── accounts/          # Gestión de usuarios
│   ├── policies/          # Gestión de pólizas
│   ├── claims/           # Gestión de siniestros
│   ├── invoices/         # Facturación
│   ├── assets/           # Bienes
│   ├── companies/        # Compañías aseguradoras
│   ├── brokers/          # Corredores
│   ├── reports/          # Reportes
│   ├── notifications/    # Notificaciones
│   └── audit/            # Auditoría
├── static/                # Archivos estáticos
│   ├── css/
│   ├── js/
│   └── img/
├── media/                 # Archivos subidos
├── templates/             # Templates HTML
└── staticfiles/           # Archivos recolectados
```

## 🔧 Configuración Avanzada

### Configuración de Email

Para activar el envío de emails, configura las variables en `.env`:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password
```

### Configuración de Base de Datos

Para cambiar a PostgreSQL en producción:

```python
# En settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}
```

### Configuración de Redis (Cache)

Para activar Redis como sistema de cache:

```python
# En settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/',
    }
}
```

## 📚 Documentación Adicional

### APIs
- Endpoints REST disponibles en desarrollo
- Documentación automática con Swagger/OpenAPI

### Testing
- Tests unitarios para modelos
- Tests de integración para workflows
- Cobertura de código con Coverage.py

### Despliegue
- Configuración para Docker
- Scripts de despliegue para AWS/GCP
- Configuración de Nginx + Gunicorn

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🧪 Datos de Prueba

El sistema ha sido poblado con datos ficticios para facilitar las pruebas. Los datos incluyen:

### Usuarios de Prueba
| Usuario | Contraseña | Rol | Descripción |
|---------|------------|-----|-------------|
| `admin` | `admin123` | Administrador | Acceso completo al sistema + Panel Django Admin |
| `gerente_seguros` | `password123` | Gerente de Seguros | Gestión de pólizas y siniestros |
| `analista_financiero` | `password123` | Analista Financiero | Gestión financiera y facturación |
| `consultor` | `password123` | Consultor | Acceso de solo lectura |
| `custodio1` | `password123` | Custodio | Facultad de Ingeniería |
| `custodio2` | `password123` | Custodio | Facultad de Ciencias Administrativas |
| `custodio3` | `password123` | Custodio | Biblioteca Central |

### Datos de Muestra
- **5 Compañías Aseguradoras**: Pichincha, Sucre, Pichincha (del), Equinoccial, Rocafuerte
- **3 Corredores**: Corredores Unidos, Asesores Financieros, Consultores de Riesgo
- **5 Pólizas**: Diferentes tipos (patrimoniales, personas) con diversos valores
- **5 Bienes/Activos**: Equipos electrónicos, vehículos, biblioteca digital
- **4+ Siniestros**: En diferentes estados (reportado, evaluación, liquidado, pagado)
- **5 Facturas**: Con cálculos automáticos de primas, IVA y descuentos
- **5 Notificaciones**: Alertas de sistema, vencimientos y actualizaciones

### Funcionalidades Implementadas
- ✅ **Autenticación y Autorización**: Sistema completo con roles y permisos
- ✅ **Gestión de Pólizas**: CRUD completo con documentos adjuntos
- ✅ **Gestión de Siniestros**: Workflow completo, timeline y documentos + Creación de nuevos siniestros
- ✅ **Facturación Automática**: Cálculos de primas, IVA y descuentos
- ✅ **Gestión de Bienes**: Inventario con custodios y seguros + Detalle completo de activos
- ✅ **Sistema de Notificaciones**: Alertas automáticas
- ✅ **Auditoría Completa**: Registro de todas las acciones
- ✅ **Reportes**: Sistema básico de reportes
- ✅ **API REST**: Endpoints para integración
- ✅ **Interface Moderna**: Bootstrap 5 responsive
- ✅ **Configuración Financiera Avanzada**: Derechos de emisión y retenciones editables
- ✅ **Comunicación Automática Externa**: Sistema de emails simulado con plantillas
- ✅ **Gestión Formal de Finiquitos**: Control completo del proceso de pago de siniestros

### Acceso al Sistema
1. Iniciar el servidor: `python manage.py runserver`
2. Acceder a: `http://localhost:8000`
3. Iniciar sesión con cualquiera de las credenciales arriba

## 📞 Soporte

Para soporte técnico o preguntas:
- Email: soporte@utpl.edu.ec
- Wiki interno: [Enlace a documentación]

## 🔄 Versiones

### v1.0.0 (Actual)
- Implementación completa de arquitectura MVC
- Sistema de autenticación y permisos
- Gestión de pólizas, siniestros y facturación
- Auditoría completa
- Interface moderna con Bootstrap 5

---

**Universidad Técnica Particular de Loja - 2026*
