# 🚀 Pipelines CI/CD - Sistema de Gestión de Seguros

Este proyecto incluye pipelines CI/CD completos para automatizar pruebas, linting, seguridad y despliegue.

## 📋 Pipelines Disponibles

### 1. GitHub Actions (`.github/workflows/ci.yml`)

Pipeline completo que se ejecuta automáticamente en cada push y pull request.

**Características:**
- ✅ Linting con flake8, black e isort
- ✅ Tests con cobertura de código
- ✅ Verificaciones de seguridad (safety, bandit)
- ✅ Verificación de migraciones
- ✅ Build y verificación de despliegue
- ✅ Integración con PostgreSQL para tests

**Ejecución:**
Se ejecuta automáticamente cuando:
- Haces push a `main`, `develop` o `master`
- Creas un pull request hacia estas ramas

**Ver resultados:**
1. Ve a la pestaña "Actions" en tu repositorio de GitHub
2. Selecciona el workflow que quieres ver
3. Revisa los resultados de cada job

### 2. GitLab CI (`.gitlab-ci.yml`)

Pipeline equivalente para proyectos en GitLab.

**Características:**
- ✅ Mismas funcionalidades que GitHub Actions
- ✅ Integración con servicios de GitLab
- ✅ Reportes de cobertura integrados

**Ejecución:**
Se ejecuta automáticamente en cada commit en GitLab CI/CD.

### 3. Script CI Local (`scripts/ci.sh`)

Script para ejecutar el pipeline localmente antes de hacer commit.

**Uso:**
```bash
# Dar permisos de ejecución (solo la primera vez)
chmod +x scripts/ci.sh

# Ejecutar el pipeline
./scripts/ci.sh
```

**Qué hace:**
- Verifica Python
- Crea/activa entorno virtual
- Instala dependencias
- Ejecuta linting (flake8, black, isort)
- Verifica migraciones
- Ejecuta tests
- Verifica seguridad (safety, bandit)

### 4. Pre-commit Hooks (`.pre-commit-config.yaml`)

Hooks de Git para ejecutar verificaciones antes de cada commit.

**Instalación:**
```bash
# Instalar pre-commit
pip install pre-commit

# Instalar los hooks
pre-commit install

# Ejecutar manualmente en todos los archivos
pre-commit run --all-files
```

**Qué hace:**
- Elimina espacios en blanco al final de líneas
- Asegura que los archivos terminen con nueva línea
- Verifica formato YAML, JSON, TOML
- Ejecuta black, isort y flake8
- Verifica seguridad con bandit

## 🔧 Configuración

### Variables de Entorno para CI

Los pipelines usan las siguientes variables de entorno (configuradas automáticamente en CI):

```bash
SECRET_KEY=test-secret-key-for-ci
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=seguros_db_test
DB_USER=seguros_user
DB_PASSWORD=seguros_pass
DB_HOST=localhost  # o 'postgres' en GitLab CI
DB_PORT=5432
```

### Configuración de Herramientas

Las herramientas de linting y formato están configuradas en `pyproject.toml`:

- **Black**: Longitud de línea 127 caracteres
- **isort**: Perfil compatible con black
- **flake8**: Máxima complejidad 10, línea máxima 127
- **Bandit**: Excluye migrations y venv

## 📊 Estructura del Pipeline

```
Pipeline CI/CD
├── Lint Stage
│   ├── flake8 (verificación de código)
│   ├── black (formato de código)
│   └── isort (orden de imports)
│
├── Test Stage
│   ├── Verificación de migraciones
│   ├── Aplicación de migraciones
│   ├── Collectstatic
│   ├── Django system check
│   └── Tests con cobertura
│
├── Security Stage
│   ├── safety (vulnerabilidades conocidas)
│   └── bandit (análisis estático de seguridad)
│
└── Build Stage
    ├── Verificación de migraciones
    ├── Build de archivos estáticos
    └── Verificación de despliegue
```

## 🐛 Solución de Problemas

### El pipeline falla en linting

**Problema:** Black o isort encuentran problemas de formato.

**Solución:**
```bash
# Formatear código automáticamente
black .
isort .
```

### El pipeline falla en tests

**Problema:** Los tests fallan o no se encuentran.

**Solución:**
```bash
# Ejecutar tests localmente
python manage.py test

# Ver más detalles
python manage.py test --verbosity=2
```

### El pipeline falla en migraciones

**Problema:** Hay migraciones pendientes.

**Solución:**
```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

### El pipeline falla en seguridad

**Problema:** Safety o Bandit encuentran vulnerabilidades.

**Solución:**
```bash
# Ver vulnerabilidades
safety check

# Actualizar dependencias vulnerables
pip install --upgrade <paquete-vulnerable>

# Revisar reporte de Bandit
cat bandit-report.json
```

## 📈 Mejores Prácticas

1. **Ejecuta el pipeline local antes de hacer push:**
   ```bash
   ./scripts/ci.sh
   ```

2. **Usa pre-commit hooks:**
   ```bash
   pre-commit install
   ```

3. **Mantén las dependencias actualizadas:**
   ```bash
   pip list --outdated
   pip install --upgrade <paquete>
   pip freeze > requirements.txt
   ```

4. **Revisa los resultados del pipeline antes de mergear PRs**

5. **Mantén la cobertura de tests alta (>80%)**

## 🔄 Flujo de Trabajo Recomendado

1. **Crear rama de feature:**
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```

2. **Desarrollar y hacer commits:**
   ```bash
   git add .
   git commit -m "Agregar nueva funcionalidad"
   # Los pre-commit hooks se ejecutarán automáticamente
   ```

3. **Verificar localmente antes de push:**
   ```bash
   ./scripts/ci.sh
   ```

4. **Push y crear PR:**
   ```bash
   git push origin feature/nueva-funcionalidad
   ```

5. **El pipeline se ejecutará automáticamente en GitHub/GitLab**

6. **Revisar resultados y corregir si es necesario**

7. **Mergear cuando el pipeline pase**

## 📝 Notas Adicionales

- Los pipelines están configurados para **permitir fallos** en algunas verificaciones (linting, seguridad) para no bloquear el desarrollo, pero es recomendable corregirlos.
- La cobertura de código se genera automáticamente y se puede ver en los artifacts del pipeline.
- Los reportes de seguridad se guardan como artifacts y están disponibles por 7-30 días según la plataforma.

## 🆘 Soporte

Si tienes problemas con los pipelines:
1. Revisa los logs en GitHub Actions o GitLab CI
2. Ejecuta el script local para debuggear
3. Verifica que todas las dependencias estén instaladas
4. Asegúrate de que las variables de entorno estén configuradas correctamente
