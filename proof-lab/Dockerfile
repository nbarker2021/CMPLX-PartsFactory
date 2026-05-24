FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PROOF_LAB_ROOT=/workspace/CMPLX-PartsFactory
ENV PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/CMPLX-PartsFactory

COPY proof-lab/requirements.txt /tmp/proof-lab-requirements.txt
RUN pip install --no-cache-dir -r /tmp/proof-lab-requirements.txt

# Entry installs editable packages from mounted repo at runtime.
COPY proof-lab/scripts/entrypoint.sh /usr/local/bin/proof-lab-entrypoint.sh
RUN chmod +x /usr/local/bin/proof-lab-entrypoint.sh

EXPOSE 8871
ENTRYPOINT ["/usr/local/bin/proof-lab-entrypoint.sh"]
