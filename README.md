# CryptoFlow - Trading Bot con Grafos y ML

Sistema de trading automatizado basado en grafos con optimización por Machine Learning.

## 🚀 Características

- **Editor Visual de Grafos**: Diseña estrategias arrastrando y conectando nodos
- **Nodos Personalizables**: Nodos de transición (condiciones) y acción (buy/sell/hold)
- **Una moneda por nodo**: Cada símbolo solo puede estar en un estado a la vez
- **ML para Optimización**: Graph Neural Networks para afinar parámetros
- **Backtesting**: Prueba tus estrategias con datos históricos
- **Multi-Exchange**: Soporte para Binance, Bybit, OKX y más

## 📁 Estructura

```
├── src/                    # Frontend React
│   ├── components/
│   │   ├── nodes/         # Componentes de nodos
│   │   ├── editor/        # Editor de grafos
│   │   └── layout/        # Layout y navegación
│   ├── pages/             # Páginas principales
│   ├── stores/            # Estado global (Zustand)
│   └── api/               # Cliente API
│
├── backend/               # Backend FastAPI
│   ├── app/
│   │   ├── api/          # Endpoints REST
│   │   ├── core/         # Configuración y DB
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── engine/       # Motor de grafos
│   │   ├── services/     # Exchange, Market Data
│   │   └── ml/           # Machine Learning
│   └── requirements.txt
│
├── backup/                # Proyecto anterior (respaldo)
└── docker-compose.yml     # Servicios Docker
```

## 🛠️ Instalación

### Con Docker (Recomendado)
```bash
docker-compose up -d
```

### Manual
```bash
# Frontend
npm install && npm run dev

# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 🌐 URLs
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
