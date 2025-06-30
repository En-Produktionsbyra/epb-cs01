FROM python:3.11-slim

WORKDIR /app

# Installera system-dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopiera requirements
COPY requirements.txt .

# Kopiera populate scriptet
COPY populate_directories_migration.py .

# Installera Python-dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera applikationskod
COPY . .

# Skapa data-katalog
RUN mkdir -p /app/data

# Exponera port
EXPOSE 8000

# Starta FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]