# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY src/ ./src/
COPY public/ ./public/
COPY index.html vite.config.js tailwind.config.js postcss.config.js ./

# Build the frontend
RUN npm run build

# Stage 2: Python Backend + Frontend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/dist ./static

# Create a main.py that serves both API and static files
RUN echo 'import os\n\
from fastapi import FastAPI\n\
from fastapi.staticfiles import StaticFiles\n\
from fastapi.responses import FileResponse\n\
from app.api import graphs, trading, nodes\n\
from app.core.config import settings\n\
\n\
app = FastAPI(title="CryptoFlow")\n\
\n\
# API routes\n\
app.include_router(graphs.router, prefix="/api/graphs", tags=["graphs"])\n\
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])\n\
app.include_router(nodes.router, prefix="/api/nodes", tags=["nodes"])\n\
\n\
# Serve static files\n\
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")\n\
\n\
@app.get("/favicon.svg")\n\
async def favicon():\n\
    return FileResponse("static/favicon.svg")\n\
\n\
@app.get("/vite.svg")\n\
async def vite():\n\
    return FileResponse("static/vite.svg")\n\
\n\
@app.get("/{full_path:path}")\n\
async def serve_spa(full_path: str):\n\
    # For SPA routing, serve index.html for all non-API routes\n\
    file_path = f"static/{full_path}"\n\
    if os.path.isfile(file_path):\n\
        return FileResponse(file_path)\n\
    return FileResponse("static/index.html")\n\
' > main.py

# Expose port
EXPOSE 8080

ENV PORT=8080
ENV GOOGLE_CLOUD_PROJECT=handheldlabs

# Start uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
