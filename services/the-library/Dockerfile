FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir numpy fastapi uvicorn
COPY server.py .
RUN mkdir -p /data/library
EXPOSE 8838
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
CMD ["python", "/app/server.py"]
