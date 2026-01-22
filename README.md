# SmartBuddy Web

Página web frontend configurada con Vite + React

## Instalación

```bash
npm install
```

## Desarrollo

```bash
npm run dev
```

Se ejecutará en `http://localhost:5173`

## Build para Producción

```bash
npm run build
```

Genera los archivos optimizados en la carpeta `dist/`

## Integración con Backend Python

La configuración proxy en `vite.config.js` redirige las peticiones `/api/*` al backend Python en `localhost:8000`

Ejemplo de uso en componentes:

```javascript
fetch('/api/endpoint')
  .then(res => res.json())
  .then(data => console.log(data))
```

## Deploy en Render

1. Conecta tu repositorio a Render
2. Configura el comando build: `npm install && npm run build`
3. Configura el comando start: `npm run serve` o usa un servidor estático

### Alternativa: Usando un servidor Python para servir los archivos

```python
from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='dist', static_url_path='')

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    if os.path.isfile(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
```

## Estructura del Proyecto

```
web/
├── src/
│   ├── main.jsx          # Punto de entrada
│   ├── App.jsx           # Componente principal
│   ├── App.css           # Estilos
│   └── index.css         # Estilos globales
├── public/               # Archivos estáticos
├── index.html            # HTML principal
├── package.json
├── vite.config.js        # Configuración Vite
└── .env                  # Variables de entorno
```

## Variables de Entorno

Crea un archivo `.env`:

```
VITE_API_URL=http://localhost:8000
```

Y úsalo en tu código:

```javascript
const API_URL = import.meta.env.VITE_API_URL
```
