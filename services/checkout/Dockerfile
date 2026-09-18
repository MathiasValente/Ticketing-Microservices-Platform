FROM python:3.11-slim

WORKDIR /app

COPY services/checkout/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common /app/services/common
COPY services/checkout /app/services/checkout

EXPOSE 8004

CMD ["uvicorn", "services.checkout.main:app", "--host", "0.0.0.0", "--port", "8004"]
