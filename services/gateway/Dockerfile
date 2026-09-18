FROM python:3.11-slim

WORKDIR /app

# Copy shared dependencies and service requirements
COPY services/gateway/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common /app/services/common
COPY services/gateway /app/services/gateway

EXPOSE 8001

CMD ["uvicorn", "services.gateway.main:app", "--host", "0.0.0.0", "--port", "8001"]
