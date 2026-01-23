# 🔐 Sistema de Gestión de Seguros UTPL - Credenciales y Guía de Inicio

## 📋 Descripción

Este documento contiene las credenciales de acceso al sistema y las instrucciones para poblar la base de datos con datos de prueba.

---

## 🚀 Configuración Inicial

### 1. Poblar la Base de Datos

Para cargar datos de prueba (usuarios, pólizas, siniestros, bienes), ejecute:

```bash
python manage.py seed_database
```

Para limpiar y recargar todos los datos:

```bash
python manage.py seed_database --clear
```

### 2. Iniciar el Servidor

```bash
python manage.py runserver
```

Acceda a la aplicación en: **http://localhost:8000**

---

## 👤 Credenciales de Usuario

### Administradores (Acceso Total)

| Usuario | Contraseña | Nombre | Departamento |
|---------|------------|--------|--------------|
| `admin` | `Admin123!` | Administrador del Sistema | TI |
| `carlos.admin` | `Admin123!` | Carlos Rodríguez Mendoza | Administración |

**Permisos:**
- ✅ Gestión completa de usuarios
- ✅ Gestión de pólizas, compañías y corredores
- ✅ Revisión y validación de siniestros
- ✅ Gestión y asignación de bienes/activos
- ✅ Acceso a reportes y configuración

---

### Gerentes de Seguros (Gestión de Pólizas y Siniestros)

| Usuario | Contraseña | Nombre | Departamento |
|---------|------------|--------|--------------|
| `maria.gerente` | `Gerente123!` | María García López | Seguros |
| `juan.gerente` | `Gerente123!` | Juan Pérez Sánchez | Seguros |

**Permisos:**
- ✅ Consulta de usuarios
- ✅ Gestión de pólizas y coberturas
- ✅ Revisión y validación de siniestros
- ✅ Consulta de bienes (solo lectura)
- ❌ NO puede crear siniestros (solo revisarlos)
- ❌ NO puede gestionar bienes

---

### Custodios de Bienes (Usuarios Operativos)

| Usuario | Contraseña | Nombre | Departamento |
|---------|------------|--------|--------------|
| `ana.custodio` | `Custodio123!` | Ana García Martínez | Facultad de Ingeniería |
| `luis.custodio` | `Custodio123!` | Luis Torres Ramírez | Facultad de Ciencias |
| `sofia.custodio` | `Custodio123!` | Sofía Mendoza Vargas | Biblioteca Central |
| `pedro.custodio` | `Custodio123!` | Pedro Sánchez Rivera | Lab. de Computación |

**Permisos:**
- ✅ Reportar siniestros de sus bienes asignados
- ✅ Ver y editar sus siniestros
- ✅ Consultar sus bienes asignados
- ❌ NO puede validar/aprobar siniestros
- ❌ NO puede gestionar pólizas

---

## 📊 Datos de Prueba Incluidos

### Compañías de Seguros
- Seguros Equinoccial S.A.
- ACE Seguros S.A.
- Seguros del Pichincha S.A.

### Corredores de Seguros
- Tecniseguros S.A.
- Asertec Brokers

### Pólizas
| Tipo | Estado | Vigencia |
|------|--------|----------|
| Vehículos | Activa | 1 año |
| Equipo Electrónico | Activa | 1 año |
| Incendio | Activa | 1 año |
| Robo | Activa | 1 año |

### Bienes/Activos
| Código | Tipo | Custodio | Asegurado |
|--------|------|----------|-----------|
| ASSET-001 | Vehículo (Toyota Hilux) | ana.custodio | ✅ |
| ASSET-002 | Vehículo (Chevrolet D-Max) | luis.custodio | ✅ |
| ASSET-003 | Equipo (Impresora HP) | ana.custodio | ✅ |
| ASSET-004 | Equipo (Dell OptiPlex) | sofia.custodio | ✅ |
| ASSET-005 | Equipo (MacBook Pro) | pedro.custodio | ✅ |
| ASSET-006 | Servidor Dell | ana.custodio | ✅ |
| ASSET-007 | Mobiliario | luis.custodio | ❌ |
| ASSET-008 | Proyector Epson | sofia.custodio | ✅ |

### Siniestros de Prueba
| Estado | Descripción |
|--------|-------------|
| Pendiente | Colisión vehicular |
| En Revisión | Falla eléctrica en impresora |
| Requiere Cambios | Robo de computador |

---

## 🔄 Flujo de Estados de Siniestros

```
┌─────────────┐
│  PENDIENTE  │ ← Custodio reporta siniestro
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌───────────────────┐
│ EN REVISIÓN │────►│ REQUIERE CAMBIOS  │
└──────┬──────┘     └─────────┬─────────┘
       │                      │
       │                      │ (Custodio corrige)
       │                      ▼
       │            ┌─────────────┐
       │◄───────────│  PENDIENTE  │
       │            └─────────────┘
       ▼
┌─────────────┐
│  APROBADO   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  LIQUIDADO  │ ← Se genera finiquito
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   PAGADO    │ ← Proceso completado
└─────────────┘

Estados finales: PAGADO, RECHAZADO
```

---

## 🛠️ Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Poblar base de datos
python manage.py seed_database

# Limpiar y poblar base de datos
python manage.py seed_database --clear

# Ejecutar servidor
python manage.py runserver
```

---

## 📞 Soporte

Para soporte técnico, contacte al equipo de desarrollo.

---

*Última actualización: Enero 2026*
