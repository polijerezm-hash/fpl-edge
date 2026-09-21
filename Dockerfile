# Build React Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/apps/web
COPY apps/web/package*.json ./
RUN npm install
COPY apps/web/ ./
RUN npm run build

# Production Python FastAPI Server
FROM python:3.11-slim
WORKDIR /app

# Install CBC solver for PuLP and curl
RUN apt-get update && apt-get install -y --no-install-recommends coinor-cbc curl && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Copy compiled frontend from frontend-builder stage
COPY --from=frontend-builder /app/apps/web/dist ./apps/web/dist

EXPOSE 8000

# Start server using the dynamic PORT provided by cloud environments (default 8000)
CMD ["sh", "-c", "uvicorn services.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
