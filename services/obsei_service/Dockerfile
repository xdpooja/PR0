FROM python:3.10-slim

WORKDIR /app

# Install system deps required by some NLP libs (keep minimal; extend if build fails)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/obsei_service/requirements-obsei.txt /app/requirements-obsei.txt
RUN pip install --no-cache-dir -r /app/requirements-obsei.txt

COPY services/obsei_service /app/services/obsei_service

ENV PYTHONUNBUFFERED=1
EXPOSE 5001

CMD ["uvicorn", "services.obsei_service.main:app", "--host", "0.0.0.0", "--port", "5001"]
