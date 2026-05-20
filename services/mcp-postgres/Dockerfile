# Minimal MCP Postgres Stub
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask psycopg2-binary
COPY <<'EOF' /app/server.py
from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/health')
def health(): return jsonify({'status':'healthy','service':'mcp-postgres'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('MCP_POSTGRES_PORT','8920')))
EOF
EXPOSE 8920
CMD ["python","/app/server.py"]
