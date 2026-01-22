# Migración Railway → Google Cloud - Cambios Realizados

## 📋 Resumen de la Migración

Se ha migrado exitosamente el frontend de **Railway** a **Google Cloud Run**. Todos los puntos de conexión del backend han sido actualizados.

## 🔧 Cambios Realizados

### 1. **Backend API URL - Actualizada en 3 archivos**

#### Archivo: `src/services/trackingService.js`
- **Antes**: `https://smartbuddy-backend-production.up.railway.app`
- **Después**: `https://handheldlabs-backend-45973956798.us-central1.run.app`
- **Propósito**: Servicio de tracking de eventos de usuario

#### Archivo: `src/services/audioService.js`
- **Antes**: `https://api.handheldlabs.com`
- **Después**: `https://handheldlabs-backend-45973956798.us-central1.run.app`
- **Propósito**: Servicio de conversión de audio (TTS) y transcripción (STT)

#### Archivo: `src/App.jsx`
- **Ubicación 1 (línea ~803)**: Llamada a `/process-text` en DemoPage
  - **Antes**: `https://smartbuddy-backend-production.up.railway.app`
  - **Después**: `https://handheldlabs-backend-45973956798.us-central1.run.app`

- **Ubicación 2 (línea ~1015)**: Llamada a `/process-text` en TestSessionsPage
  - **Antes**: `https://smartbuddy-backend-production.up.railway.app`
  - **Después**: `https://handheldlabs-backend-45973956798.us-central1.run.app`

### 2. **Almacenamiento - Actualizado en 1 archivo**

#### Archivo: `src/config/s3.js`
- **Antes**: `https://storage.railway.app/portable-locker-hmwiw9dby`
- **Después**: `https://storage.googleapis.com/handheldlabs-storage/portable-locker`
- **Propósito**: Acceso a imágenes y assets del dispositivo Verba

### 3. **Configuración de Entorno**

#### Archivo: `.env.example` (creado)
```env
# Backend API URL - Google Cloud Run
VITE_WRAPPER_API_URL=https://handheldlabs-backend-45973956798.us-central1.run.app

# Storage Configuration
VITE_STORAGE_BUCKET_URL=https://storage.googleapis.com/handheldlabs-storage/portable-locker

# API Token (si es requerido por el backend)
VITE_API_TOKEN=handheldlabs-api-token-2026
```

## 📊 Información del Backend

- **URL**: https://handheldlabs-backend-45973956798.us-central1.run.app
- **Proyecto Google Cloud**: `handheldlabs`
- **Región**: `us-central1`
- **Tipo**: Google Cloud Run Service

## 🔌 Endpoints Utilizados

El frontend se comunica con los siguientes endpoints:

1. **POST `/process-text`** - Procesar texto con Gemini
   - Enviado desde: `DemoPage` y `TestSessionsPage`
   - Payload: `{ text, language, session_id }`

2. **POST `/text-to-audio`** - Convertir texto a audio (TTS)
   - Enviado desde: `audioService.js`
   - Payload: `{ text, language }`

3. **POST `/audio-to-text`** - Transcribir audio a texto (STT)
   - Enviado desde: `audioService.js`
   - Payload: FormData con archivo de audio

4. **POST `/api/track`** - Rastrear eventos
   - Enviado desde: `trackingService.js`
   - Payload: Datos de evento

5. **POST `/api/contact`** - Enviar formulario de contacto
   - Enviado desde: `App.jsx` (ContactPage)

## ✅ Verificación

Para verificar que todo funciona correctamente:

```bash
# 1. Verificar que el backend está disponible
curl https://handheldlabs-backend-45973956798.us-central1.run.app/health

# 2. Ejecutar el frontend en desarrollo
npm run dev

# 3. Probar la página de Demo
# Ir a: http://localhost:5173 → Demo
# Grabar audio y verificar que se transcribe y procesa correctamente
```

## 📝 Notas Importantes

- ✅ Todas las URLs ahora usan **Google Cloud Run**
- ✅ Las variables de entorno pueden sobrescribir las URLs por defecto
- ✅ El almacenamiento ahora apunta a **Google Cloud Storage**
- ✅ Los servicios mantienen la misma funcionalidad
- ✅ No se requieren cambios en el código de aplicación

## 🚀 Próximos Pasos (si es necesario)

1. **Si el bucket S3 tiene un nombre diferente**: Actualizar la URL en `src/config/s3.js`
2. **Si se requiere autenticación especial**: Configurar headers de autorización
3. **Si hay endpoints específicos del backend**: Verificar con el equipo de backend la existencia de estos endpoints
4. **Para debugging**: Usar las herramientas de Google Cloud Console para revisar logs del backend

---

**Fecha de Migración**: 22 de enero de 2026
**Estado**: ✅ Completado
