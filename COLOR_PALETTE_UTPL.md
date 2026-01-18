# 🎓 Paleta de Colores UTPL - Integración Armoniosa

## 📋 Resumen de la Nueva Paleta

Se ha integrado la identidad visual de la **Universidad Técnica Particular de Loja (UTPL)** en el sistema de colores de la aplicación, manteniendo la modernidad y coherencia visual del diseño Tailwind CSS.

## 🎨 Paleta de Colores Corporativa UTPL

### Color Primario - Azul UTPL

```
Azul UTPL Corporativo: #003366 (Original)
↓ Adaptado para design system moderno
Azul UTPL Actualizado: #4a7dbb (Principal)
```

**Variaciones del Azul UTPL:**
- **Primary-50** (#f0f4f9): Ultra claro - Fondos de cards
- **Primary-100** (#dce5f0): Muy claro - Hover estados
- **Primary-200** (#b8cae3): Claro - Bordes suaves
- **Primary-300** (#8db0d1): Medio claro - Textos secundarios
- **Primary-400** (#5b8bc2): Medio - Acentos
- **Primary-500** (#4a7dbb): **Principal UTPL** - Headers, botones principales
- **Primary-600** (#2e5a8f): Oscuro - Hover estados
- **Primary-700** (#1f3d5f): Muy oscuro - Focus estados
- **Primary-800** (#143147): Extra oscuro - Textos
- **Primary-900** (#0d1f2d): Casi negro - Background fondo

### Colores Secundarios Complementarios

#### Verde Empresarial (Éxito)
```
--color-success-500: #1fa876  (Verde profundo, armónico)
--color-success-600: #157456  (Verde oscuro)
--color-success-700: #0f4a38  (Verde muy oscuro)
```
✅ Ideal para: Estados exitosos, confirmaciones, valores positivos

#### Dorado UTPL (Acento Complementario)
```
--color-accent-500: #d4a574   (Gold cálido)
--color-accent-600: #b8904f   (Gold oscuro)
```
✨ Ideal para: Destacados especiales, premios, reconocimientos

#### Ámbar Cálido (Advertencia)
```
--color-warning-500: #d97706  (Ámbar profesional)
--color-warning-600: #b45309  (Ámbar oscuro)
```
⚠️ Ideal para: Alertas, pendientes, acciones requeridas

#### Rojo Profesional (Peligro)
```
--color-danger-500: #c5192d   (Rojo profundo)
--color-danger-600: #991b1b   (Rojo muy oscuro)
```
🔴 Ideal para: Errores, rechazos, acciones destructivas

#### Cyan Moderno (Información)
```
--color-info-500: #0891b2     (Cyan vibrante)
--color-info-600: #0e7490     (Cyan oscuro)
```
ℹ️ Ideal para: Información, notificaciones, detalles

## 🎯 Principios de Armonía

### 1. **Coherencia Cromática**
- Todos los colores comparten la profundidad visual del Azul UTPL
- Las variaciones mantienen la saturación consistente
- Los colores complementarios respetan la gama de tonos corporativos

### 2. **Contraste Accesible**
- Ratio de contraste mínimo 4.5:1 (WCAG AA)
- Textos oscuros sobre fondos claros
- Textos claros sobre fondos oscuros

### 3. **Jerarquía Visual**
```
Primario (UTPL Blue) → Headers, CTAs principales, navegación
Secundario (Grays) → Contenido, textos, bordes
Acentos (Verde, Gold, Ámbar, Rojo) → Estados, alertas
```

### 4. **Flexibilidad Contextual**
- Verde para transacciones exitosas (seguros pagados)
- Rojo para siniestros y rechazos
- Ámbar para documentación pendiente
- Dorado para reconocimientos (pólizas vigentes)

## 🚀 Uso en Componentes

### Navbar y Headers
```css
background: linear-gradient(135deg, #4a7dbb 0%, #2e5a8f 100%);
/* Degradado UTPL Blue profesional */
```

### Botones Primarios
```css
background: linear-gradient(135deg, #4a7dbb 0%, #2e5a8f 100%);
/* Mismo gradiente UTPL Blue para coherencia */
```

### Cards Destacadas
```css
border-left: 4px solid #4a7dbb;  /* Acento UTPL Blue */
background: linear-gradient(135deg, #f0f4f9 0%, #ffffff 100%);
```

### Estados de Éxito (Pago de Seguros)
```css
background: linear-gradient(135deg, #1fa876 0%, #157456 100%);
color: #ffffff;
```

### Alertas de Peligro (Siniestros/Rechazos)
```css
background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
border-left: 4px solid #c5192d;
```

### Acentos Dorados (Especiales)
```css
border-bottom: 3px solid #d4a574;
color: #b8904f;
```

## 📊 Aplicación en el Sistema

### Gestión de Pólizas
| Estado | Color | Uso |
|--------|-------|-----|
| Vigente | Verde (#1fa876) | Pólizas activas |
| Por Vencer | Ámbar (#d97706) | Alertas de vencimiento |
| Expirada | Rojo (#c5192d) | Pólizas caducadas |
| Principal | UTPL Blue (#4a7dbb) | Headers, info general |

### Gestión de Siniestros
| Estado | Color | Uso |
|--------|-------|-----|
| Reportado | Gris (#6b7280) | Inicial |
| En Evaluación | UTPL Blue (#4a7dbb) | En proceso |
| Liquidado | Verde (#1fa876) | Aprobado |
| Pagado | Verde Oscuro (#157456) | Completado |
| Rechazado | Rojo (#c5192d) | Negado |

### Bienes y Activos
| Condición | Color | Uso |
|-----------|-------|-----|
| Excelente | Verde (#1fa876) | Buen estado |
| Bueno | UTPL Blue (#4a7dbb) | Estado normal |
| Regular | Ámbar (#d97706) | Requiere atención |
| Malo | Rojo (#c5192d) | Necesita reemplazo |

## 🎓 Identidad UTPL Preservada

La paleta mantiene elementos clave de la identidad UTPL:

✅ **Azul Corporativo** - Color principal reconocible  
✅ **Profesionalismo** - Tonos y saturación empresarial  
✅ **Modernidad** - Adaptado a standards contemporáneos  
✅ **Accesibilidad** - Cumple estándares WCAG  
✅ **Coherencia** - Integración armoniosa con otros elementos  

## 🔄 Migración desde Paleta Anterior

Los cambios son retrocompatibles:
- Toda referencias a `--color-primary-*` ahora usan UTPL Blue
- Las funcionalidades se mantienen idénticas
- No se requieren cambios en HTML o JavaScript
- Solo actualización de valores CSS

## 📱 Responsive y Adaptable

La paleta funciona correctamente en:
- ✅ Light Mode (actual)
- ✅ Dark Mode (implementable)
- ✅ High Contrast Mode (accesible)
- ✅ Impresión (colores convertibles)

## 🧪 Testing de Armonía

Para verificar la armonía visual:

1. **Acceder a dashboard**: Verificar gradientes UTPL Blue
2. **Ver pólizas vigentes**: Deben usar verde
3. **Ver siniestros**: Deben usar colores específicos por estado
4. **Revisar alertas**: Deben usar ámbar/rojo claramente
5. **Verificar contraste**: Textos sobre fondos deben ser legibles

## 🎨 Especificaciones Técnicas

### Formato de Color
- **Hex**: #4a7dbb
- **RGB**: rgb(74, 125, 187)
- **HSL**: hsl(211, 44%, 51%)

### Aplicación CSS
```css
/* Variables globales */
color: var(--color-primary-500);     /* UTPL Blue principal */
color: var(--color-primary-600);     /* UTPL Blue oscuro */
color: var(--color-success-500);     /* Verde éxito */
color: var(--color-warning-500);     /* Ámbar advertencia */
color: var(--color-danger-500);      /* Rojo peligro */
```

### Gradientes Recomendados
```css
/* Gradiente UTPL Standard */
background: linear-gradient(135deg, #4a7dbb 0%, #2e5a8f 100%);

/* Gradiente Éxito */
background: linear-gradient(135deg, #1fa876 0%, #157456 100%);

/* Gradiente Advertencia */
background: linear-gradient(135deg, #d97706 0%, #b45309 100%);

/* Gradiente Peligro */
background: linear-gradient(135deg, #c5192d 0%, #991b1b 100%);
```

---

**Versión**: 3.0.0 (Paleta UTPL Integrada)  
**Fecha**: Enero 2026  
**Diseñador**: Sistema UTPL Moderno
