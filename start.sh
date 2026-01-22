#!/bin/bash
# Script para iniciar el servidor en producción

PORT=${PORT:-3000}
npm run build
npx serve -s dist -l $PORT
