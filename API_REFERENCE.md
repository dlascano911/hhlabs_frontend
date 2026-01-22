# Backend API - Guía de Referencia Rápida

## 🌐 Base URL

```
https://handheldlabs-backend-45973956798.us-central1.run.app
```

## 📍 Endpoints Disponibles

### 1. Health Check
**GET** `/health`

Verifica que el servicio esté funcionando.

**Respuesta:**
```json
{
  "status": "ok",
  "service": "handheldlabs-backend",
  "timestamp": 1737587234.56
}
```

**Ejemplo curl:**
```bash
curl https://handheldlabs-backend-45973956798.us-central1.run.app/health
```

---

### 2. Procesar Texto con Gemini
**POST** `/process-text`

Envía texto para procesarlo con Gemini AI. Mantiene contexto conversacional por sesión.

**Body:**
```json
{
  "text": "¿Cuál es la capital de Francia?",
  "session_id": "abc123",  // opcional, se genera automáticamente si no se envía
  "language": "es"  // opcional, detectado automáticamente
}
```

**Respuesta:**
```json
{
  "success": true,
  "input": "¿Cuál es la capital de Francia?",
  "response": "La capital de Francia es París, una ciudad conocida por su arte, moda y cultura.",
  "session_id": "abc123",
  "topic_changed": false,
  "topics": ["geografía-francia", "capitales"]
}
```

**Ejemplo curl:**
```bash
curl -X POST https://handheldlabs-backend-45973956798.us-central1.run.app/process-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hola, ¿cómo estás?",
    "session_id": "test-123"
  }'
```

---

### 3. Tracking de Usuarios
**POST** `/api/track`

Registra acciones de usuarios para analytics.

**Body:**
```json
{
  "session_id": "abc123",
  "action": "page_view",
  "conversion": false,
  "referrer": "https://google.com",
  "page_url": "https://handheldlabs.com/chat"
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Tracking registrado"
}
```

---

### 4. Debug MySQL
**GET** `/api/debug-mysql`

Ver registros de tracking en la base de datos (útil para debugging).

**Respuesta:**
```json
{
  "success": true,
  "connection": "OK",
  "config": {
    "host": "...",
    "port": 3306,
    "user": "root",
    "database": "railway"
  },
  "total_records": 150,
  "records": [...]
}
```

---

### 5. Debug Sesiones
**GET** `/api/debug/sessions`

Ver todas las sesiones conversacionales guardadas.

**Respuesta:**
```json
{
  "success": true,
  "sessions": [
    {
      "id": "uuid",
      "session_uuid": "abc123",
      "message": "Hola",
      "response": "¡Hola! ¿En qué puedo ayudarte?",
      "context": "...",
      "tokens": 150,
      "cost": "0.00001500",
      "tags": "[\"conversación\", \"saludo\"]",
      "date_creation": "2026-01-22 10:30:00"
    }
  ]
}
```

---

### 6. Texto a Audio (Proxy)
**POST** `/api/text-to-audio`

Convierte texto a audio usando Handheld Labs API.

**Body:**
```json
{
  "text": "Hola, este es un mensaje de prueba",
  "voice": "en_US-amy-medium"
}
```

---

### 7. Audio a Texto (Proxy)
**POST** `/api/audio-to-text`

Transcribe audio a texto usando Whisper.

**Content-Type:** `multipart/form-data`

**Form Data:**
- `audio`: archivo de audio

---

### 8. Formulario de Contacto
**POST** `/api/contact`

Envía mensaje de contacto.

**Body:**
```json
{
  "from_name": "Juan Pérez",
  "from_email": "juan@example.com",
  "message": "Me interesa su servicio",
  "to": "diego@handheldlabs.com",
  "cc": "dlascano91@gmail.com"
}
```

---

## 🔑 Variables de Entorno del Servicio

El backend usa las siguientes variables de entorno (ya configuradas en Cloud Run):

```bash
# Google Gemini
GOOGLE_API_KEY=AIzaSyALRjv7gE1DDhVMkGNQkU80x9gGu8hUyqo

# MySQL (Railway)
MYSQL_URL=mysql://user:pass@host:port/database
MYSQLHOST=...
MYSQLPORT=3306
MYSQLUSER=root
MYSQLPASSWORD=...
MYSQL_DATABASE=railway

# Handheld Labs API
VERBA_API_TOKEN=handheldlabs-api-token-2026

# Server
PORT=8000
```

## 📦 Arquitectura del Código

```
app/
├── config/          # Configuración (settings.py)
├── database/        # Conexiones MySQL, tracking, sesiones
├── services/        # Gemini AI, geolocalización
├── handlers/        # Manejadores de endpoints
├── utils/           # Utilidades HTTP
└── models/          # Modelos de datos (futuro)
```

Ver [README_STRUCTURE.md](README_STRUCTURE.md) para más detalles.

## 🔄 Flujo de Conversación con Contexto

1. **Primera interacción**: 
   - Usuario envía texto sin `session_id`
   - Backend genera nuevo `session_id`
   - Guarda mensaje sin contexto previo

2. **Interacciones subsecuentes**:
   - Usuario envía texto con el mismo `session_id`
   - Backend recupera contexto acumulado
   - Gemini usa el contexto para responder
   - Se guarda nuevo mensaje con contexto actualizado

3. **Cambio de tema**:
   - Si Gemini detecta cambio de tema (`topic_changed: true`)
   - Backend busca sesiones previas con tags similares
   - Si encuentra, continúa esa sesión
   - Si no, crea nueva sesión

4. **Expiración**:
   - Sesiones expiran después de 5 minutos de inactividad
   - `is_expired: true` reinicia el contexto

## 🧪 Testing con curl

### Test completo de conversación:

```bash
# Primera pregunta
curl -X POST https://handheldlabs-backend-45973956798.us-central1.run.app/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "¿Cuál es la capital de Italia?"}' | jq

# Guarda el session_id de la respuesta y úsalo en la siguiente pregunta

# Pregunta de seguimiento (usa el mismo session_id)
curl -X POST https://handheldlabs-backend-45973956798.us-central1.run.app/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "¿Y cuál es su población?", "session_id": "abc123"}' | jq
```

## 📊 Costos de Gemini

El backend usa `gemini-2.5-flash-lite`:
- **Costo por token input**: $0.000015 / 1K tokens
- **Costo por token output**: $0.00006 / 1K tokens
- Promedio por conversación: ~$0.000001 - $0.00001

Todos los costos se registran en la tabla `user_session`.

## 🔍 Debugging

### Ver logs en tiempo real:

```bash
gcloud run services logs tail handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs
```

### Ver últimos 100 logs:

```bash
gcloud run services logs read handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs \
  --limit=100
```

### Buscar errores:

```bash
gcloud run services logs read handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs \
  --limit=500 | grep "ERROR\|❌"
```

## 🚨 Errores Comunes

### 403 Forbidden
**Causa**: Servicio no público
**Solución**: Ejecutar comando del Paso 4 en [SETUP_GOOGLE_CLOUD.md](SETUP_GOOGLE_CLOUD.md)

### Error de conexión MySQL
**Causa**: Variables de entorno incorrectas o MySQL caído
**Solución**: Verificar variables con `gcloud run services describe`

### Timeout
**Causa**: Proceso tomó más de 60 segundos
**Solución**: Aumentar timeout en Cloud Run o optimizar código

### Error de Gemini API
**Causa**: API key inválida o quota excedida
**Solución**: Verificar API key en Google Cloud Console

## 📞 Soporte

Para problemas o preguntas:
- **Email**: dlascano91@gmail.com
- **Logs**: Ver con gcloud (comandos arriba)
- **Console**: https://console.cloud.google.com/run?project=handheldlabs

## 🔗 Enlaces Útiles

- **Backend URL**: https://handheldlabs-backend-45973956798.us-central1.run.app
- **Console Cloud Run**: https://console.cloud.google.com/run/detail/us-central1/handheldlabs-backend
- **GitHub Repo**: https://github.com/dlascano911/hhlabs_backend
- **Gemini API Docs**: https://ai.google.dev/docs
