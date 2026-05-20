# Minimal MMDB Unified Stub
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask psycopg2-binary
COPY <<'EOF' /app/server.py
from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/health')
def health(): return jsonify({'status':'healthy','service':'mmdb-unified'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT','8084')))
EOF
EXPOSE 8084
CMD ["python","/app/server.py"]
