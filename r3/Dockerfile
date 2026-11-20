FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# node.py imports rrr_control at startup: ship both or the container crashes.
COPY node.py rrr_control.py ./

ENV R3_DATA_DIR=/data
VOLUME ["/data"]
EXPOSE 8000

# Honour the platform-assigned PORT (Railway health checks probe it); 8000 locally.
CMD ["sh", "-c", "exec uvicorn node:app --host 0.0.0.0 --port ${PORT:-8000}"]
