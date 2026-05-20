# Minimal SpeedLight API Stub
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask
COPY <<'EOF' /app/server.py
from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/health')
def health(): return jsonify({'status':'healthy','service':'speedlight-api'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('SPEEDLIGHT_PORT','8843')))
EOF
EXPOSE 8843
CMD ["python","/app/server.py"]
