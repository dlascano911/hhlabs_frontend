# 🚀 Guía de Inicio Rápido - Feature de Carga de Audio

## ⚡ 5 Pasos para Comenzar

### 1️⃣ Configura las variables de entorno

```bash
cd /workspaces/smartbuddy/web
```

Crea o edita el archivo `.env`:

```env
# URL del servicio de transcripción de audio remoto
VITE_AUDIO_SERVICE_URL=https://3isx66up2rqdjm-8000.proxy.runpod.net

# URL del backend Wrapper (para Gemini)
VITE_WRAPPER_API_URL=http://localhost:8000
```

### 2️⃣ Instala dependencias (si es primera vez)

```bash
npm install
```

### 3️⃣ Inicia el servidor de desarrollo

```bash
npm run dev
```

Verás algo como:
```
VITE v4.x.x  ready in 100 ms

➜  Local:   http://localhost:5173/
```

### 4️⃣ Abre en tu navegador

Ve a: **http://localhost:5173**

### 5️⃣ ¡Usa la aplicación!

```
Opción A: Cargar archivo
├─ Haz clic en "📂 Seleccionar archivo"
├─ Elige un archivo de audio (wav, mp3, flac, etc.)
└─ La transcripción y respuesta de Gemini aparecerán automáticamente

Opción B: Grabar audio (requiere permiso del navegador)
├─ Haz clic en "🎤 Iniciar Grabación"
├─ Habla cerca del micrófono
├─ Haz clic en "⏹️ Detener"
└─ Espera la transcripción y respuesta de Gemini
```

---

## 📋 Requisitos Previos

✅ Node.js 16+
✅ Servicio de audio running en `https://3isx66up2rqdjm-8000.proxy.runpod.net`
✅ Backend Wrapper running en `http://localhost:8000` (desarrollo) o en Railway (producción)

---

## 🔍 Verificar Conexión

Abre la consola del navegador (F12) y deberías ver:

```
🔗 Wrapper API URL: http://localhost:8000
🔗 Audio Service URL: https://3isx66up2rqdjm-8000.proxy.runpod.net
✅ Backend conectado: {...}
✅ Audio Service conectado: {...}
```

---

## ❌ Solucionar Problemas

### Error: "Audio Service Unavailable"

```bash
# Verifica que el servicio esté running
curl https://3isx66up2rqdjm-8000.proxy.runpod.net/health
```

Si no responde, verifica `VITE_AUDIO_SERVICE_URL` en tu `.env`

### Error: "Backend Unavailable"

```bash
# Asegúrate de que el wrapper está corriendo
curl http://localhost:8000/
```

Si no responde, inicia el wrapper:
```bash
cd ../wrapper
python main.py
```

### Error: "CORS policy"

Verifica en la consola del navegador. Puede significar que los servicios no están accesibles desde el navegador. Esto es común en ciertos ambientes de red.

---

## 📚 Documentación Completa

Para más detalles, consulta:
- [AUDIO_UPLOAD_FEATURE.md](./AUDIO_UPLOAD_FEATURE.md) - Documentación completa
- [CAMBIOS.md](./CAMBIOS.md) - Resumen de cambios técnicos

---

## 🎯 Ejemplo de Flujo Completo

```
1. Selecciono archivo: "entrevista.mp3"
   ↓
2. El navegador muestra: "📁 Archivo seleccionado: entrevista.mp3 (2.5 MB)"
   ↓
3. Hago clic en "🚀 Transcribir"
   ↓
4. Muestra: "⏳ Transcribiendo audio..."
   ↓
5. Después de 5-10 segundos, aparece:
   "Texto transcrito: [texto aquí...]"
   ↓
6. Automáticamente muestra: "🤖 Procesando con Gemini..."
   ↓
7. Después de 2-3 segundos, aparece la respuesta:
   "🤖 Respuesta de Gemini: [respuesta aquí...]"
```

---

## ✨ Características

✅ Cargar archivos de audio desde el disco
✅ Grabar audio con el micrófono
✅ Transcripción automática
✅ Integración con Gemini
✅ Interfaz intuitiva
✅ Manejo de errores
✅ Estado de conexión en tiempo real

---

## 🚀 Comandos Útiles

```bash
# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview

# Limpiar node_modules
rm -rf node_modules && npm install
```

---

## 💡 Tips

- Usa archivos de audio de menos de 5 minutos para mejor rendimiento
- El navegador necesita permiso para acceder al micrófono si grabas audio
- Las respuestas de Gemini dependen de tu API key configurada en el wrapper
- Puedes copiar las respuestas con el botón "📋 Copiar respuesta"

---

¡Ya está! 🎉 Tu aplicación está lista. ¿Necesitas ayuda?
