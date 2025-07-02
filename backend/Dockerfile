FROM python:3.11-slim

WORKDIR /app

# Installera system-dependencies (lägg till curl)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Kopiera requirements
COPY requirements.txt .

# Installera Python-dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera applikationskod
COPY . .

# Skapa data-katalog
RUN mkdir -p /app/data

# Exponera port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Starta FastAPI (ta bort --reload för produktion)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]