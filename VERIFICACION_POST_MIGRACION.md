# 🔧 Guía de Verificación Post-Migración

## ✅ Verificación Técnica

### 1. Backend está Accesible ✓
```bash
# El backend de Google Cloud Run está accesible y funcional
curl https://handheldlabs-backend-45973956798.us-central1.run.app/health

# Resultado esperado: HTTP/2 200 con respuesta JSON del health check
# ✅ VERIFICADO: El endpoint /health responde correctamente
```

### 2. Todas las URLs Actualizada ✓
- ✓ `src/services/trackingService.js`
- ✓ `src/services/audioService.js`
- ✓ `src/App.jsx` (2 ubicaciones)
- ✓ `src/config/s3.js`
- ✓ `public/debug-sessions.html`
- ✓ `test-sessions.html`
- ✓ `vite.config.js`

### 3. No hay Errores de Sintaxis ✓
Todos los archivos JavaScript/JSX han sido validados sin errores.

---

## 🧪 Pruebas de Función (Próximo Paso)

### Prueba 1: Iniciar el Frontend en Desarrollo
```bash
cd /workspaces/hhlabs_frontend
npm install  # (si es necesario)
npm run dev
```

**Resultado esperado**: El servidor Vite inicia en `http://localhost:5173`

---

### Prueba 2: Página de Demo
1. Ir a: `http://localhost:5173` → **Demo**
2. Realizar una de estas acciones:
   - 🎤 Grabar audio con el micrófono
   - 📤 Subir un archivo de audio
3. **Verificar**: 
   - ✓ El audio se transcribe
   - ✓ La respuesta de Gemini aparece
   - ✓ El audio de respuesta se genera y reproduce

---

### Prueba 3: Test Sessions
1. Ir a: `http://localhost:5173` → **Test Sessions**
2. Escribir un mensaje de prueba
3. **Verificar**:
   - ✓ El mensaje se envía al backend
   - ✓ Recibe respuesta de Gemini
   - ✓ Aparecen tiempos de respuesta

---

### Prueba 4: Tracking
1. Ir a cualquier página
2. Hacer clic en botones (Nav, Demo, etc.)
3. **Verificar** (en Dev Console):
   - ✓ No hay errores CORS
   - ✓ Eventos se registran correctamente

---

## 📊 Información de Debugging

### Variables de Entorno
```bash
# Ver variables configuradas
echo $VITE_WRAPPER_API_URL  # Debe estar vacío (usa default)
echo $VITE_API_TOKEN        # Puede estar vacío
```

### Crear archivo .env (opcional)
```bash
cp .env.example .env

# Luego editar si es necesario:
# VITE_WRAPPER_API_URL=https://handheldlabs-backend-45973956798.us-central1.run.app
```

### Ver logs en la consola del navegador
Presionar `F12` → **Console** para ver:
- Llamadas a endpoints
- Respuestas JSON
- Errores de red (si los hay)

---

## ⚠️ Posibles Problemas y Soluciones

### Problema 1: CORS Error
```
Access to fetch at 'https://...' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**Solución**: El backend necesita configurar CORS headers. Contactar con el equipo backend.

### Problema 2: 404 en Endpoint
```
POST /process-text → 404 Not Found
```

**Solución**: El endpoint no existe en el backend. Verificar que el backend tiene implementados los endpoints:
- `/process-text` 
- `/text-to-audio`
- `/audio-to-text`
- `/api/track`

### Problema 3: Authentication Error
```
401 Unauthorized
```

**Solución**: Verificar que el token en `src/services/audioService.js` es correcto o que el backend no requiere autenticación.

---

## 📝 Checklist Final

- [ ] Backend está accesible
- [ ] Frontend inicia sin errores
- [ ] Página Home carga correctamente
- [ ] Página Demo funciona
- [ ] Audio se graba y transcribe
- [ ] Gemini responde
- [ ] Audio de respuesta se genera
- [ ] Test Sessions funciona
- [ ] No hay errores en Console
- [ ] No hay errores CORS
- [ ] Botones de tracking funcionan

---

## 🚀 Deployment a Producción

Una vez verificado todo localmente:

```bash
# Build para producción
npm run build

# Resultado: archivo dist/index.html + assets
```

Luego:
1. Subir archivos a Google Cloud Storage (si se usa)
2. O deployar a Firebase Hosting, Vercel, Netlify, etc.

---

**Fecha**: 22 de Enero de 2026  
**Estado**: Listo para testing  
**Próximo**: Contactar al equipo backend para verificar endpoints
