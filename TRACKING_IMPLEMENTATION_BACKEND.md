# 📊 Especificación de Tracking - Para Backend

## 📋 Descripción General

Sistema de tracking para registrar todas las acciones del usuario en la web Verba. El frontend envía eventos al backend mediante llamadas POST al endpoint `/api/track`.

---

## 🔧 Implementación Actual (Frontend)

### Archivo: `src/services/trackingService.js`

```javascript
const API_URL = import.meta.env.VITE_WRAPPER_API_URL || 'https://handheldlabs-backend-45973956798.us-central1.run.app';

class TrackingService {
  constructor() {
    this.sessionId = this.getOrCreateSessionId();
  }

  // Generar UUID v4 simple (compatible con navegadores)
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  // Obtener o crear session_id único con UUID
  getOrCreateSessionId() {
    let sessionId = sessionStorage.getItem('session_id');
    if (!sessionId) {
      sessionId = this.generateUUID();
      sessionStorage.setItem('session_id', sessionId);
    }
    return sessionId;
  }

  // Enviar evento de tracking
  async track(action, conversion = false) {
    try {
      const data = {
        session_id: this.sessionId,
        action,
        conversion,
        referrer: document.referrer || '',
        page_url: window.location.href
      };

      const response = await fetch(`${API_URL}/api/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.warn('❌ Tracking failed:', errorText);
        return false;
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('❌ Error sending tracking:', error);
      return false;
    }
  }

  // Métodos específicos para diferentes acciones
  trackPageView(page) {
    return this.track(`page_view:${page}`);
  }

  trackClick(element) {
    return this.track(`click:${element}`);
  }

  trackPurchase(product) {
    return this.track(`purchase:${product}`, true);
  }

  trackDemo() {
    return this.track('demo_started');
  }

  trackContact() {
    return this.track('contact_submitted');
  }

  trackNavigation(from, to) {
    return this.track(`navigation:${from}_to_${to}`);
  }

  trackScroll(depth) {
    return this.track(`scroll:${depth}%`);
  }

  trackTimeOnPage(seconds) {
    return this.track(`time_on_page:${seconds}s`);
  }

  trackFormStart(formName) {
    return this.track(`form_start:${formName}`);
  }

  trackFormAbandoned(formName) {
    return this.track(`form_abandoned:${formName}`);
  }

  trackVideo(action, videoId) {
    return this.track(`video_${action}:${videoId}`);
  }

  trackError(errorType, errorMsg) {
    return this.track(`error:${errorType}:${errorMsg.substring(0, 100)}`);
  }

  trackSearch(query) {
    return this.track(`search:${query}`);
  }
}

export const trackingService = new TrackingService();
```

---

## 🔌 API Endpoint del Backend

### POST `/api/track`

**URL**: `https://handheldlabs-backend-45973956798.us-central1.run.app/api/track`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "click:nav_demo",
  "conversion": false,
  "referrer": "https://example.com",
  "page_url": "https://handheldlabs.com/?page=home"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "Event tracked successfully",
  "event_id": "evt_123456789",
  "timestamp": "2026-01-22T12:34:56Z"
}
```

**Response (Error)**:
```json
{
  "success": false,
  "error": "Invalid session_id"
}
```

---

## 📊 Tipos de Eventos

| Evento | Descripción | Conversion |
|--------|-------------|-----------|
| `page_view:{page}` | Usuario visualiza página | No |
| `click:{element}` | Click en elemento | No |
| `purchase:{product}` | Compra realizada | **SÍ** |
| `demo_started` | Demo iniciada | No |
| `contact_submitted` | Formulario de contacto enviado | No |
| `navigation:{from}_to_{to}` | Navegación entre páginas | No |
| `scroll:{depth}%` | Scroll a profundidad | No |
| `time_on_page:{seconds}s` | Tiempo en página | No |
| `form_start:{formName}` | Inicio de formulario | No |
| `form_abandoned:{formName}` | Formulario abandonado | No |
| `video_{action}:{videoId}` | Acciones de video | No |
| `error:{type}:{message}` | Error en app | No |
| `search:{query}` | Búsqueda realizada | No |

---

## 🎯 Datos Recolectados

### Por evento:
- ✅ `session_id` - UUID único por sesión
- ✅ `action` - Tipo de acción realizada
- ✅ `conversion` - Booleano si es conversión
- ✅ `referrer` - De dónde vino el usuario
- ✅ `page_url` - URL actual del sitio
- ✅ `timestamp` - (generado por backend)

### En el backend se puede agregar:
- IP del usuario
- User Agent
- Geolocalización
- Información de dispositivo
- Duración de sesión

---

## 💾 Almacenamiento (Backend)

Sugerencia de estructura en BD:

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
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (session_id),
  INDEX (created_at),
  INDEX (is_conversion)
);

CREATE TABLE user_sessions (
  session_id UUID PRIMARY KEY,
  first_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_visit TIMESTAMP,
  event_count INT DEFAULT 0,
  conversion_count INT DEFAULT 0,
  INDEX (first_visit)
);
```

---

## 🔗 Dónde se Usa en Frontend

### Llamadas Actuales:

1. **App.jsx - Página View**
   ```javascript
   useEffect(() => {
     trackingService.trackPageView(currentPage);
   }, [currentPage]);
   ```

2. **App.jsx - Navegación**
   ```javascript
   const handlePageChange = (page) => {
     trackingService.trackNavigation(currentPage, page);
     setCurrentPage(page);
   };
   ```

3. **App.jsx - Logo Click**
   ```javascript
   onClick={() => { 
     trackingService.trackClick('logo'); 
     handlePageChange('home'); 
   }}
   ```

4. **App.jsx - Nav Links**
   ```javascript
   onClick={() => { 
     trackingService.trackClick('nav_pricing'); 
     handlePageChange('pricing'); 
   }}
   ```

5. **App.jsx - CTA Button**
   ```javascript
   onClick={() => { 
     trackingService.trackClick('cta_preorder'); 
     setCurrentPage('cart'); 
   }}
   ```

6. **App.jsx - Specs**
   ```javascript
   trackingService.trackClick('view_specs');
   ```

7. **App.jsx - Purchase**
   ```javascript
   trackingService.trackPurchase(productName);
   ```

8. **App.jsx - Contact Form**
   ```javascript
   trackingService.trackContact();
   ```

9. **App.jsx - Demo**
   ```javascript
   trackingService.trackDemo();
   ```

---

## 📝 Schema de Datos Completo

```typescript
interface TrackingEvent {
  session_id: string;        // UUID
  action: string;            // Tipo de acción
  conversion: boolean;       // Es una conversión
  referrer: string;          // URL de referencia
  page_url: string;          // URL actual
  user_agent?: string;       // (backend)
  ip_address?: string;       // (backend)
  timestamp?: string;        // (backend)
  event_id?: string;         // (backend)
  location?: {
    country?: string;
    city?: string;
    coordinates?: {
      lat: number;
      lon: number;
    };
  };
  device?: {
    type: string;            // 'mobile' | 'tablet' | 'desktop'
    os: string;              // 'iOS' | 'Android' | 'Windows' | 'macOS'
    browser: string;
  };
}
```

---

## 🔐 Consideraciones de Seguridad

1. **Validación**: El backend debe validar que `session_id` es un UUID válido
2. **Rate Limiting**: Limitar eventos por sesión (ej: 1000/hora)
3. **Data Privacy**: Hashear IPs si se almacenan
4. **GDPR**: Permitir descargar y eliminar datos personales
5. **Retention**: Establecer política de eliminación (ej: 90 días)

---

## 📈 Queries Útiles (Backend)

```sql
-- Eventos más populares
SELECT action, COUNT(*) as count FROM tracking_events 
GROUP BY action ORDER BY count DESC;

-- Conversiones por sesión
SELECT session_id, COUNT(*) as event_count, SUM(is_conversion) as conversions 
FROM tracking_events GROUP BY session_id;

-- Usuarios nuevos hoy
SELECT COUNT(DISTINCT session_id) FROM tracking_events 
WHERE DATE(created_at) = CURRENT_DATE;

-- Tasa de conversión
SELECT 
  SUM(CASE WHEN is_conversion THEN 1 ELSE 0 END)::float / COUNT(*) as conversion_rate
FROM tracking_events;
```

---

## ✅ Próximos Pasos

1. **Backend**: Implementar endpoint POST `/api/track`
2. **Backend**: Crear tablas de almacenamiento
3. **Backend**: Agregar validaciones y rate limiting
4. **Frontend**: Simplificar tracking (solo llamar al backend)
5. **Analytics**: Crear dashboard de reportes

