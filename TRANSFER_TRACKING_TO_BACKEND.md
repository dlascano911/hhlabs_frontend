# 📥 ARCHIVOS PARA TRANSFERIR AL BACKEND

## 📋 Resumen

He preparado toda la documentación y especificación del sistema de tracking para que la transfieras al equipo backend. El frontend ya está simplificado y listo.

---

## 📁 Archivos a Transferir

### 1. **TRACKING_BACKEND_SPEC.md** (PRINCIPAL)
Este es el archivo que debe leer el equipo backend. Contiene:
- ✅ Especificación del endpoint `/api/track`
- ✅ Schema de request/response
- ✅ Ejemplos de eventos
- ✅ Validaciones requeridas
- ✅ Checklist de implementación
- ✅ Queries de analytics

**Destinatario**: Equipo de Backend  
**Acción**: Implementar endpoint POST `/api/track`

### 2. **TRACKING_IMPLEMENTATION_BACKEND.md** (COMPLEMENTARIO)
Documentación técnica más detallada:
- ✅ Descripción general del sistema
- ✅ Implementación actual del frontend
- ✅ Tipos de eventos completos
- ✅ Schema SQL sugerido
- ✅ Consideraciones de seguridad
- ✅ GDPR compliance

**Destinatario**: Equipo de Backend / Tech Lead  
**Acción**: Referencia técnica

---

## 🔧 Cambios Realizados en Frontend

### Archivo Modificado: `src/services/trackingService.js`

**Cambios**:
- ✅ Simplificado a "fire-and-forget" (sin await)
- ✅ Mejor rendimiento
- ✅ No bloquea UX
- ✅ Mantiene mismos métodos públicos

**Código clave**:
```javascript
fetch(`${API_URL}/api/track`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
}).catch(err => console.warn('⚠️ Tracking error:', err.message));

return true; // No espera respuesta
```

---

## 📊 Eventos Que Frontend Envía

### Eventos de Navegación
```
page_view:home
page_view:pricing
page_view:demo
page_view:cart
page_view:contact
page_view:test-sessions
```

### Eventos de Click
```
click:logo
click:nav_home
click:nav_pricing
click:nav_demo
click:nav_contact
click:nav_test_sessions
click:cta_preorder
click:view_specs
```

### Eventos de Navegación Entre Páginas
```
navigation:home_to_demo
navigation:home_to_pricing
navigation:pricing_to_demo
(etc... para todas las transiciones)
```

### Eventos de Compra (IMPORTANTES - conversion=true)
```
purchase:Verba_Standard
purchase:Verba_One_Premium
```

### Otros Eventos
```
demo_started
contact_submitted
```

---

## 🔌 Endpoint Backend Requerido

```
POST /api/track

URL: https://handheldlabs-backend-45973956798.us-central1.run.app/api/track

Headers:
  Content-Type: application/json

Request Body:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "click:nav_demo",
  "conversion": false,
  "referrer": "https://example.com",
  "page_url": "https://handheldlabs.com"
}

Response:
{
  "success": true,
  "message": "Event tracked successfully",
  "event_id": "evt_123456789",
  "timestamp": "2026-01-22T12:34:56Z"
}
```

---

## ✅ Checklist para Backend

- [ ] Crear endpoint POST `/api/track`
- [ ] Validar campos de entrada (session_id es UUID)
- [ ] Rate limiting (max 1000 eventos/sesión/hora)
- [ ] Crear tabla `tracking_events`
- [ ] Crear tabla `user_sessions`
- [ ] Agregar CORS headers
- [ ] Implementar logging
- [ ] Error handling
- [ ] Tests unitarios
- [ ] Tests de carga
- [ ] Documentar API
- [ ] Setup de monitoring

---

## 📈 Ejemplo de Flujo de Compra

```
1. Usuario en página Home
   → Frontend: trackingService.trackPageView('home')
   → Backend: INSERT INTO tracking_events (session_id, 'page_view:home', false)

2. Usuario hace click en "Pre-Order"
   → Frontend: trackingService.trackClick('cta_preorder')
   → Backend: INSERT INTO tracking_events (session_id, 'click:cta_preorder', false)

3. Usuario navega a Cart
   → Frontend: trackingService.trackNavigation('home', 'cart')
   → Backend: INSERT INTO tracking_events (session_id, 'navigation:home_to_cart', false)

4. Usuario compra
   → Frontend: trackingService.trackPurchase('Verba_Standard')
   → Backend: INSERT INTO tracking_events (session_id, 'purchase:Verba_Standard', true)
   → Backend: UPDATE user_sessions SET conversion_count = conversion_count + 1

Result:
  ✓ 4 eventos en BD
  ✓ 1 conversión registrada
  ✓ session_id agrupa todo el flujo
```

---

## 🔐 Consideraciones de Seguridad

### En Backend Debe Validar:
- ✅ UUID válido en `session_id`
- ✅ `action` no vacío
- ✅ `conversion` es boolean
- ✅ URLs son HTTPS
- ✅ Rate limiting por session_id
- ✅ No guardar datos sensibles
- ✅ GDPR compliance

### Datos a NO Almacenar:
- ❌ Contraseñas
- ❌ Tokens de API
- ❌ Números de tarjeta
- ❌ Información identificable personal
- ❌ Datos sensibles en URLs

---

## 📝 Notas Importantes

1. **Session ID**: Generado por frontend (UUID), persiste durante sesión del usuario
2. **Fire-and-Forget**: Frontend no espera respuesta, mejor UX
3. **Backend Persiste**: Backend responsable de guardar en BD
4. **Conversiones**: Solo eventos con `conversion: true` son compras
5. **Analytics**: Con esta data se pueden hacer reportes potentes

---

## 🚀 Verificación en Frontend

Para verificar que todo funciona:

```bash
# 1. Iniciar frontend
npm run dev

# 2. Abrir DevTools (F12)
# 3. Ir a Console
# 4. Hacer clic en botones
# 5. Deberías ver logs de tracking en la consola

# 6. (Cuando backend esté listo)
# 7. Verificar en DB que los eventos fueron guardados
```

---

## 📞 Contacto

Si el equipo backend tiene preguntas:
1. Revisar `TRACKING_BACKEND_SPEC.md` (especificación completa)
2. Revisar `TRACKING_IMPLEMENTATION_BACKEND.md` (detalles técnicos)
3. Ver ejemplos de eventos en este archivo
4. Verificar endpoint `/api/track` está respondiendo

---

**Status**: ✅ Frontend listo para transferencia  
**Archivos**: 2 (TRACKING_BACKEND_SPEC.md + TRACKING_IMPLEMENTATION_BACKEND.md)  
**Fecha**: 22 de Enero de 2026

