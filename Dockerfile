# ==============================================================================
# DOCKERFILE PARA RAILWAY/RENDER - Sistema RAG
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema necesarias para chromadb/pypdf
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Directorios persistentes
RUN mkdir -p /data/uploads /data/chroma

EXPOSE 8080

CMD ["sh", "-c", "uvicorn api.index:app --host 0.0.0.0 --port ${PORT:-8080}"]
