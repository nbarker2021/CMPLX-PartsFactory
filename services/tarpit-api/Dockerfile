# Minimal TarPit API Stub
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask
COPY <<'EOF' /app/server.py
from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/health')
def health(): return jsonify({'status':'healthy','service':'tarpit-api'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('TARPIT_PORT','8844')))
EOF
EXPOSE 8844
CMD ["python","/app/server.py"]
