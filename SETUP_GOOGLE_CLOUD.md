# Setup Google Cloud CLI - Guía Completa

Esta guía permite a cualquier agente o desarrollador configurar acceso completo al backend de Handheld Labs en Google Cloud Run.

## 📋 Información del Proyecto

- **Proyecto ID**: `handheldlabs`
- **Proyecto Number**: `45973956798`
- **Servicio**: `handheldlabs-backend`
- **Región**: `us-central1`
- **URL del Backend**: https://handheldlabs-backend-45973956798.us-central1.run.app

## 🔧 Paso 1: Instalar Google Cloud CLI

### En Linux/Dev Container (Ubuntu):

```bash
# Descargar e instalar
curl https://sdk.cloud.google.com | bash

# Recargar el shell
exec -l $SHELL

# Verificar instalación
gcloud --version
```

### Si gcloud no está en el PATH:

```bash
# Agregar al PATH manualmente
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# Para hacerlo permanente, agregar al ~/.bashrc
echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 🔐 Paso 2: Autenticarse en Google Cloud

```bash
# Iniciar autenticación
gcloud auth login
```

Esto abrirá una ventana del navegador donde debes:
1. Iniciar sesión con tu cuenta de Google
2. Permitir acceso a Google Cloud SDK
3. Copiar el código de verificación

**Cuenta requerida**: `dlascano91@gmail.com`

## 🎯 Paso 3: Configurar el Proyecto

```bash
# Listar proyectos disponibles
gcloud projects list

# Configurar el proyecto handheldlabs
gcloud config set project handheldlabs

# Verificar configuración
gcloud config list
```

Deberías ver:
```
[core]
account = dlascano91@gmail.com
project = handheldlabs
```

## 🌐 Paso 4: Hacer el Servicio Público (Si es necesario)

Si el servicio no es accesible públicamente (error 403 Forbidden):

```bash
gcloud run services add-iam-policy-binding handheldlabs-backend \
  --region=us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --project=handheldlabs
```

Salida esperada:
```
Updated IAM policy for service [handheldlabs-backend].
bindings:
- members:
  - allUsers
  role: roles/run.invoker
```

## 📊 Paso 5: Verificar el Servicio

### Ver información del servicio:

```bash
gcloud run services describe handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs
```

### Ver logs en tiempo real:

```bash
gcloud run services logs read handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs \
  --limit=50
```

### Ver logs en streaming:

```bash
gcloud run services logs tail handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs
```

## 🚀 Paso 6: Deploys y Actualizaciones

### Ver revisiones/deploys:

```bash
gcloud run revisions list \
  --service=handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs
```

### Ver últimos deploys:

```bash
gcloud run operations list \
  --region=us-central1 \
  --project=handheldlabs
```

### Forzar un nuevo deploy:

```bash
# Cloud Run redeploys automáticamente cuando hay push a main
# Pero si necesitas forzar un redeploy:
gcloud run services update handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs
```

## 🔍 Paso 7: Probar el Backend

### Health check:

```bash
curl https://handheldlabs-backend-45973956798.us-central1.run.app/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "service": "handheldlabs-backend",
  "timestamp": 1737587234.56
}
```

### Probar endpoint principal:

```bash
curl -X POST https://handheldlabs-backend-45973956798.us-central1.run.app/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola, ¿cómo estás?"}'
```

## 📝 Comandos Útiles Adicionales

### Ver variables de entorno del servicio:

```bash
gcloud run services describe handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs \
  --format="value(spec.template.spec.containers[0].env)"
```

### Actualizar variables de entorno:

```bash
gcloud run services update handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs \
  --set-env-vars="NEW_VAR=value"
```

### Ver configuración de escalado:

```bash
gcloud run services describe handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs \
  --format="yaml(spec.template.spec.containerConcurrency)"
```

### Cambiar recursos (CPU/Memoria):

```bash
gcloud run services update handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs \
  --memory=512Mi \
  --cpu=1
```

## 🔄 Integración Continua

El backend está configurado para **deploy automático**:

1. Cada `git push` a la rama `main` dispara un deploy automático
2. Google Cloud Build construye la imagen desde el Dockerfile
3. Cloud Run actualiza el servicio con la nueva imagen
4. El proceso toma ~2-5 minutos

### Ver builds recientes:

```bash
gcloud builds list \
  --project=handheldlabs \
  --limit=10
```

### Ver logs de un build específico:

```bash
gcloud builds log <BUILD_ID> --project=handheldlabs
```

## 🐛 Troubleshooting

### Error: "command not found: gcloud"

```bash
# Verificar instalación
ls -la ~/google-cloud-sdk/bin/gcloud

# Agregar al PATH
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
```

### Error: "You do not have permission"

```bash
# Re-autenticarse
gcloud auth login

# Verificar cuenta activa
gcloud auth list
```

### Error: "Project not found"

```bash
# Listar proyectos disponibles
gcloud projects list

# Configurar proyecto correcto
gcloud config set project handheldlabs
```

### Servicio retorna 403 Forbidden:

```bash
# Verificar permisos IAM
gcloud run services get-iam-policy handheldlabs-backend \
  --region=us-central1 \
  --project=handheldlabs

# Hacer público si es necesario (comando del Paso 4)
```

## 📚 Recursos Adicionales

- **Documentación Cloud Run**: https://cloud.google.com/run/docs
- **gcloud CLI Reference**: https://cloud.google.com/sdk/gcloud/reference/run
- **Console Web**: https://console.cloud.google.com/run?project=handheldlabs

## ✅ Checklist de Verificación

Después de completar el setup, verifica que puedes:

- [ ] Ejecutar `gcloud --version` exitosamente
- [ ] Ver la lista de proyectos con `gcloud projects list`
- [ ] Ver el proyecto `handheldlabs` en la lista
- [ ] Describir el servicio con `gcloud run services describe`
- [ ] Acceder al endpoint `/health` exitosamente
- [ ] Ver logs del servicio
- [ ] Hacer push a main y ver el deploy automático

## 🎯 Comandos Rápidos de Referencia

```bash
# Ver servicio
gcloud run services describe handheldlabs-backend --region=us-central1

# Ver logs
gcloud run services logs read handheldlabs-backend --region=us-central1 --limit=50

# Hacer público
gcloud run services add-iam-policy-binding handheldlabs-backend --region=us-central1 --member="allUsers" --role="roles/run.invoker"

# Ver builds
gcloud builds list --limit=10

# Probar health
curl https://handheldlabs-backend-45973956798.us-central1.run.app/health
```

---

**Nota**: Esta guía asume que tienes acceso a la cuenta `dlascano91@gmail.com` y permisos en el proyecto `handheldlabs`. Si necesitas agregar otro usuario, contacta al administrador del proyecto.
