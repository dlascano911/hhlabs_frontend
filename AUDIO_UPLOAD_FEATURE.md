# Característica de Carga de Audio - SmartBuddy

## 🎯 Descripción

El frontend de SmartBuddy ha sido actualizado para soportar dos formas de obtener transcripción de audio:

1. **Cargar archivo de audio** - Sube un archivo de audio y transkribirlo
2. **Grabar audio** - Graba audio en tiempo real con tu micrófono (Web Speech API)

Ambos métodos envían el texto transcrito a Gemini y muestran la respuesta.

## 🔄 Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. Selecciona archivo de audio O graba con micrófono      │
│     ↓                                                       │
│  2. Envía archivo a servicio de transcripción remoto       │
│     (endpoint: /audio-to-text en AUDIO_SERVICE_URL)        │
│     ↓                                                       │
│  3. Obtiene texto transcrito                               │
│     ↓                                                       │
│  4. Envía texto a backend Gemini                           │
│     (endpoint: /process-text en WRAPPER_API_URL)           │
│     ↓                                                       │
│  5. Muestra respuesta de Gemini en la interfaz             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuración

### Variables de Entorno

Crea un archivo `.env` en la carpeta `web/` (o actualiza el existente):

```env
# URL del servicio de transcripción de audio remoto
VITE_AUDIO_SERVICE_URL=https://3isx66up2rqdjm-8000.proxy.runpod.net

# URL del backend Wrapper (para Gemini)
# Desarrollo local:
VITE_WRAPPER_API_URL=http://localhost:8000

# Producción en Railway:
# VITE_WRAPPER_API_URL=https://smartbuddy-wrapper.railway.app
```

### Requisitos

- **Audio Service**: Debe tener el endpoint `/audio-to-text` que acepte `POST` con un archivo de audio en FormData
- **Wrapper Service**: Debe tener el endpoint `/process-text` que acepte `POST` con JSON `{text: string}`

## 📁 Estructura de Archivos

```
web/
├── src/
│   ├── App.jsx                  # Componente principal actualizado
│   ├── App.css                  # Estilos mejorados
│   ├── services/
│   │   └── audioService.js      # Servicio actualizado con nuevos métodos
│   └── main.jsx
├── .env.example                 # Ejemplo de configuración
└── vite.config.js
```

## 🆕 Nuevos Métodos en audioService

### `transcribeAudio(audioFile)`

Transcribe un archivo de audio usando el servicio remoto.

**Parámetros:**
- `audioFile`: File object del input de archivo

**Retorna:**
```javascript
{
  text: "Texto transcrito",
  language: "eng"  // opcional
}
```

**Ejemplo:**
```javascript
const file = fileInputRef.current.files[0]
const result = await audioService.transcribeAudio(file)
console.log(result.text)  // "Texto transcrito"
```

### `getAudioServiceHealth()`

Verifica si el servicio de audio está disponible.

**Retorna:**
```javascript
{
  status: "ok",
  device: "cuda",
  model: "distil-whisper/distil-large-v3",
  ...
}
```

## 🖥️ Interfaz de Usuario

### Sección 1: Cargar Archivo de Audio
- Botón **📂 Seleccionar archivo** - Abre el selector de archivos
- Botón **🚀 Transcribir** - Envía el archivo al servicio de transcripción
- Muestra nombre y tamaño del archivo seleccionado

### Sección 2: Grabar Audio (Opcional)
- Botón **🎤 Iniciar Grabación** - Comienza a grabar
- Botón **⏹️ Detener** - Detiene la grabación
- Botón **🚀 Procesar con Gemini** - Procesa el texto grabado
- Muestra el texto transcrito

### Sección 3: Resultado de Gemini
- Muestra la respuesta de Gemini
- Botón **📋 Copiar respuesta** - Copia al portapapeles
- Botón **↻ Nueva solicitud** - Limpia para hacer otra

### Barra de Estado
- Muestra si el Backend está conectado
- Muestra si el Servicio de Audio está conectado

## 🔐 Manejo de Errores

El sistema maneja los siguientes errores:

| Error | Causa | Solución |
|-------|-------|----------|
| Archivo vacío | El audio no tiene contenido | Selecciona un archivo con audio válido |
| Tipo de archivo inválido | No es un archivo de audio | Usa formatos: wav, mp3, flac, m4a, etc. |
| Audio Service Unavailable | No se puede conectar al endpoint | Verifica `VITE_AUDIO_SERVICE_URL` |
| Backend Unavailable | No se puede conectar a Gemini | Verifica `VITE_WRAPPER_API_URL` |
| Error en transcripción | El modelo falló | Intenta con otro archivo |
| Error en Gemini | Gemini no respondió | Verifica la clave API |

## 📊 Ejemplo de Flujo Completo

```
1. Usuario selecciona archivo: "entrevista.wav"
   ↓
2. Frontend envía: POST /audio-to-text con Form Data
   Audio Service ↓
3. Respuesta: {text: "Mi nombre es Juan García...", language: "spa"}
   ↓
4. Frontend envía: POST /process-text con JSON
   {text: "Mi nombre es Juan García..."}
   Wrapper/Gemini ↓
5. Respuesta: {success: true, response: "Hola Juan..."}
   ↓
6. Frontend muestra: "Hola Juan..."
```

## 🚀 Despliegue

### Desarrollo Local

```bash
cd web
npm install
npm run dev
```

Asegúrate de tener:
- `VITE_AUDIO_SERVICE_URL` apuntando al servicio de audio remoto
- `VITE_WRAPPER_API_URL=http://localhost:8000` apuntando al wrapper local

### Producción

1. Build:
```bash
npm run build
```

2. Configura las variables de entorno:
```env
VITE_AUDIO_SERVICE_URL=https://tu-audio-service.com
VITE_WRAPPER_API_URL=https://tu-wrapper-service.com
```

3. Deploy en Railway:
```bash
railroad up
```

## 📝 Notas

- El servicio de audio espera archivos en formato WAV, MP3, FLAC, etc.
- El texto transcrito se envía automáticamente a Gemini después de la transcripción
- Las respuestas se pueden copiar al portapapeles
- La aplicación muestra el estado de conexión con ambos servicios

## 🔗 Enlaces Útiles

- Audio Service Endpoint: https://3isx66up2rqdjm-8000.proxy.runpod.net/docs
- Backend Wrapper: Configura según tu setup
- Documentación de Vite: https://vitejs.dev/

## 📞 Troubleshooting

### "Audio Service Unavailable"

Verifica que:
1. La URL en `VITE_AUDIO_SERVICE_URL` sea correcta
2. El servicio esté corriendo en esa URL
3. No haya problemas de CORS (revisa la consola del navegador)

### "Backend Unavailable"

Verifica que:
1. El wrapper esté corriendo en `VITE_WRAPPER_API_URL`
2. La API key de Gemini esté configurada en el wrapper
3. No haya problemas de CORS

### El archivo no se transcribe

Verifica:
1. Que sea un archivo de audio válido (wav, mp3, flac, m4a)
2. Que el servicio de audio esté funcionando
3. La consola del navegador para más detalles del error
