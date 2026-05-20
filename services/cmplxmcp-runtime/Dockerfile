FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/module \
    CMPLXMCP_MODULE=/module

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY runtime_probe.py /app/runtime_probe.py
COPY stdio_entry.py /app/stdio_entry.py

CMD ["python", "/app/stdio_entry.py"]
