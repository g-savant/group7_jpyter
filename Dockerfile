FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend_ws_app.py start.sh recon.py ./ 
COPY lab_notebooks ./lab_notebooks

RUN pip install --no-cache-dir \
    jupyterlab==4.2.4 \
    notebook==7.2.1 \
    jupyter-server-proxy==4.1.0 \
    tornado==6.5.2 \
    "httpx<0.28" \
    && chmod +x /app/start.sh

EXPOSE 8888

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/start.sh"]
