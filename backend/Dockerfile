# Använd äldre, stabilare Python version
FROM python:3.10-bullseye

WORKDIR /app

# Uppdatera system och installera grundläggande dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Kopiera requirements först för caching
COPY requirements.txt .

# Installera Python dependencies med explicit versioner
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Kopiera applikationskod
COPY . .

# Skapa data directory med rätt permissions
RUN mkdir -p /app/data && chmod 755 /app/data

# Exponera port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Starta med explicit Python och debugging
CMD ["python", "-u", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]