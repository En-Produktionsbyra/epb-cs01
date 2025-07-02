# Använd en större base image med mer dependencies förinstallerade
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

WORKDIR /app

# Kopiera endast det vi behöver
COPY main.py /app/
COPY database/ /app/database/
COPY populate_directories_migration.py /app/

# Installera endast specifika extra dependencies som behövs
RUN pip install --no-cache-dir aiofiles python-multipart

# Skapa data directory
RUN mkdir -p /app/data

# Starta FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]