# Minimal Workforce Controller Stub
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask fastapi uvicorn
COPY <<'EOF' /app/server.py
from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/api/health')
def health(): return jsonify({'status':'healthy','service':'workforce-controller'})
@app.route('/')
def index(): return jsonify({'service':'workforce-controller','version':'0.1.0'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('CONTROLLER_PORT','8775')))
EOF
EXPOSE 8775
CMD ["python","/app/server.py"]
