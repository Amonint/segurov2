# Sistema de Gestión de Seguros - UTPL

Sistema integral de gestión de pólizas de seguros, siniestros, facturación y reportes para la Universidad Técnica Particular de Loja (UTPL).

## 📋 Descripción

Este proyecto implementa un sistema completo de gestión de seguros con arquitectura Django MVC, incluyendo:

- **Gestión de Pólizas**: CRUD completo con generación automática de números
- **Sistema de Siniestros**: Workflow completo con estados y timeline
- **Facturación Automática**: Cálculos fiscales complejos con IVA y descuentos
- **Control de Bienes**: Gestión de activos con depreciación automática
- **Sistema de Permisos**: Roles y permisos granulares
- **Auditoría Completa**: Logging automático de todas las operaciones
- **Reportes**: Sistema de reportes con exportación (en desarrollo)

## 🏗️ Arquitectura

```
django_seguros/
├── seguros/                    # Proyecto principal Django
├── apps/                      # Aplicaciones Django
│   ├── accounts/              # Gestión de usuarios y auth
│   ├── policies/              # Gestión de pólizas
│   ├── claims/                # Gestión de siniestros
│   ├── invoices/              # Facturación automática
│   ├── assets/                # Bienes/activos
│   ├── companies/             # Compañías aseguradoras
│   ├── brokers/               # Corredores
│   ├── reports/               # Reportes
│   ├── notifications/         # Sistema de notificaciones
│   └── audit/                 # Auditoría
├── static/                    # Archivos estáticos
├── media/                     # Archivos subidos
├── templates/                 # Templates HTML
└── manage.py                  # Comando Django
```

## 🚀 Inicio Rápido

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

## 📊 Funcionalidades Principales

### Gestión de Pólizas
- ✅ Creación automática de números de póliza
- ✅ Validaciones de fechas y montos
- ✅ Gestión documental
- ✅ Alertas de vencimiento

### Sistema de Siniestros
- ✅ Workflow completo con estados
- ✅ Timeline automático de eventos
- ✅ Validaciones de transiciones
- ✅ Gestión documental por tipo

### Facturación Automática
- ✅ Cálculos fiscales automáticos
- ✅ IVA 15%, derechos de emisión variables
- ✅ Descuentos pronto pago (5%)
- ✅ Retenciones configurables

### Sistema de Auditoría
- ✅ Logging automático de todas las operaciones
- ✅ Tracking de cambios (antes/después)
- ✅ Información de IP y navegador

## 🛠️ Comandos Útiles

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
| `admin` | `password123` | Administrador | Acceso completo al sistema |
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
- **3 Siniestros**: En diferentes estados (evaluación, liquidado, pagado)
- **5 Facturas**: Con cálculos automáticos de primas, IVA y descuentos
- **5 Notificaciones**: Alertas de sistema, vencimientos y actualizaciones

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

**Universidad Técnica Particular de Loja - 2024**
