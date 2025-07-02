FROM python:3.10-bullseye

WORKDIR /app

RUN pip install fastapi uvicorn

COPY test_main.py .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "test_main:app", "--host", "0.0.0.0", "--port", "8000"]
