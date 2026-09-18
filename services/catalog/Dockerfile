FROM python:3.11-slim

WORKDIR /app

COPY services/catalog/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common /app/services/common
COPY services/catalog /app/services/catalog

EXPOSE 8002

CMD ["uvicorn", "services.catalog.main:app", "--host", "0.0.0.0", "--port", "8002"]
