FROM python:3.11-slim

WORKDIR /app

COPY services/inventory/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common /app/services/common
COPY services/inventory /app/services/inventory

EXPOSE 8003

CMD ["uvicorn", "services.inventory.main:app", "--host", "0.0.0.0", "--port", "8003"]
