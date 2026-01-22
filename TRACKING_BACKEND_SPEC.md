# 🔄 TRACKING TRANSFER - Frontend → Backend

## 📋 Resumen

El sistema de tracking ha sido optimizado:
- ✅ **Frontend**: Solo genera eventos y llama al backend
- ✅ **Backend**: Responsable de persistir todos los eventos

---

## 🚀 IMPLEMENTACIÓN REQUERIDA EN BACKEND

### 1. Endpoint Requerido

```
POST /api/track
```

**URL Completa**: `https://handheldlabs-backend-45973956798.us-central1.run.app/api/track`

---

### 2. Request Body Schema

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "click:nav_demo",
  "conversion": false,
  "referrer": "https://example.com",
  "page_url": "https://handheldlabs.com/?page=home"
}
```

**Campos**:
| Campo | Tipo | Ejemplo | Descripción |
|-------|------|---------|-------------|
| `session_id` | UUID | `550e8400-e29b-...` | ID único de sesión del usuario |
| `action` | string | `click:nav_demo` | Tipo de acción (ver tabla de eventos) |
| `conversion` | boolean | `false` | True si es una compra o conversión |
| `referrer` | string | `https://example.com` | De dónde vino el usuario |
| `page_url` | string | `https://handheldlabs.com` | URL actual |

---

### 3. Response Schema

**Success (200)**:
```json
{
  "success": true,
  "message": "Event tracked successfully",
  "event_id": "evt_123456789",
  "timestamp": "2026-01-22T12:34:56Z"
}
```

**Error (400/500)**:
```json
{
  "success": false,
  "error": "Invalid session_id format"
}
```

---

### 4. Eventos Esperados

```
page_view:{page}              → Usuario visualiza página
click:{element}               → Click en elemento
purchase:{product}            → Compra realizada (conversion=true)
demo_started                  → Demo iniciada
contact_submitted             → Formulario de contacto
navigation:{from}_to_{to}     → Navegación entre páginas
scroll:{depth}%               → Scroll a profundidad
time_on_page:{seconds}s       → Tiempo en página
form_start:{formName}         → Inicio de formulario
form_abandoned:{formName}     → Formulario abandonado
video_{action}:{videoId}      → Acciones de video
error:{type}:{message}        → Error en app
search:{query}                → Búsqueda
```

---

### 5. Tabla de Base de Datos Sugerida

```sql
CREATE TABLE tracking_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  action VARCHAR(255) NOT NULL,
  is_conversion BOOLEAN DEFAULT false,
  referrer TEXT,
  page_url TEXT,
  user_agent TEXT,
  ip_address VARCHAR(45),
  country VARCHAR(2),
  city VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_session_id (session_id),
  INDEX idx_created_at (created_at),
  INDEX idx_is_conversion (is_conversion),
  FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
);

CREATE TABLE user_sessions (
  session_id UUID PRIMARY KEY,
  first_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  event_count INT DEFAULT 1,
  conversion_count INT DEFAULT 0,
  referrer TEXT,
  user_agent TEXT,
  ip_address VARCHAR(45),
  INDEX idx_first_visit (first_visit)
);
```

---

### 6. Validaciones Requeridas

- ✅ `session_id` debe ser UUID válido (36 caracteres, formato UUID)
- ✅ `action` no puede estar vacío
- ✅ `conversion` debe ser boolean
- ✅ Limitar máximo 1000 eventos por sesión por hora (rate limiting)
- ✅ Sanitizar `referrer` y `page_url` (HTTPS)

---

### 7. Seguridad y Privacy

- 🔐 Validar headers CORS
- 🔐 Hashear/anonimizar IPs si es necesario
- 🔐 GDPR: Permitir descargar datos personales
- 🔐 Retention: Establecer política de limpieza (ej: 90 días)
- 🔐 No guardar datos sensibles en `action` (parámetros de URL con tokens, etc.)

---

### 8. Datos Adicionales Opcionales (Backend puede agregar)

```typescript
{
  // ... datos del request ...
  user_agent: "Mozilla/5.0 ...",
  ip_address: "192.168.1.1",
  country: "US",
  city: "San Francisco",
  timestamp: "2026-01-22T12:34:56Z",
  device: {
    type: "desktop",
    os: "macOS",
    browser: "Chrome"
  }
}
```

---

## 📊 EJEMPLOS DE EVENTOS QUE ENVÍA FRONTEND

### Event 1: Page View
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "page_view:home",
  "conversion": false,
  "referrer": "",
  "page_url": "https://handheldlabs.com/?page=home"
}
```

### Event 2: Click en Botón
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "click:nav_demo",
  "conversion": false,
  "referrer": "https://handheldlabs.com",
  "page_url": "https://handheldlabs.com/?page=home"
}
```

### Event 3: Compra (IMPORTANTE - es conversión)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "purchase:Verba_Standard",
  "conversion": true,
  "referrer": "https://handheldlabs.com",
  "page_url": "https://handheldlabs.com/?page=cart"
}
```

### Event 4: Demo Iniciada
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "demo_started",
  "conversion": false,
  "referrer": "https://handheldlabs.com",
  "page_url": "https://handheldlabs.com/?page=demo"
}
```

---

## 🔧 CAMBIOS EN FRONTEND

### Antes (Con logs y await):
```javascript
const response = await fetch(`${API_URL}/api/track`, {...});
console.log('✅ Tracking success:', result);
return result.success;
```

### Después (Fire-and-forget, no bloquea):
```javascript
fetch(`${API_URL}/api/track`, {...})
  .catch(err => console.warn('⚠️ Tracking error:', err.message));
return true;
```

**Ventaja**: La app no espera respuesta del backend, más rápido y no bloquea UX.

---

## 📈 QUERIES ÚTILES PARA ANALYTICS

```sql
-- Top 10 eventos más populares
SELECT action, COUNT(*) as count FROM tracking_events 
GROUP BY action ORDER BY count DESC LIMIT 10;

-- Conversiones por día
SELECT DATE(created_at) as day, COUNT(*) as conversions 
FROM tracking_events WHERE is_conversion = true 
GROUP BY DATE(created_at) ORDER BY day DESC;

-- Tasa de conversión
SELECT 
  SUM(CASE WHEN is_conversion THEN 1 ELSE 0 END)::float / COUNT(*) as conversion_rate
FROM tracking_events;

-- Sesiones únicas
SELECT COUNT(DISTINCT session_id) as unique_sessions FROM tracking_events;

-- Eventos por sesión (promedio)
SELECT AVG(event_count) as avg_events_per_session FROM user_sessions;
```

---

## ✅ CHECKLIST BACKEND

- [ ] Crear endpoint POST `/api/track`
- [ ] Validar campos de entrada
- [ ] Crear tablas en BD
- [ ] Implementar rate limiting
- [ ] Agregar CORS headers
- [ ] Logs de eventos
- [ ] Error handling
- [ ] Tests unitarios
- [ ] Tests de carga
- [ ] Documentar API
- [ ] Monitoreo de uptime

---

## 🔗 REFERENCIAS

- **Documento técnico completo**: `TRACKING_IMPLEMENTATION_BACKEND.md`
- **Frontend tracking simplificado**: `src/services/trackingService.js`
- **Backend API URL**: `https://handheldlabs-backend-45973956798.us-central1.run.app`

