#!/usr/bin/env bash
set -euo pipefail

# Start Tornado backend in the background.
python backend_ws_app.py &
BACK_PID=$!

shutdown() {
  kill "$BACK_PID" 2>/dev/null || true
  if [[ -n "${JUPYTER_PID-}" ]]; then
    kill "$JUPYTER_PID" 2>/dev/null || true
  fi
}

trap shutdown SIGINT SIGTERM EXIT

AUTH_FLAGS=()
if [[ -n "${JUPYTER_TOKEN-}" ]]; then
  AUTH_FLAGS+=(--ServerApp.token="${JUPYTER_TOKEN}")
fi
if [[ -n "${JUPYTER_PASSWORD-}" ]]; then
  AUTH_FLAGS+=(--ServerApp.password="${JUPYTER_PASSWORD}")
fi

# Trust notebooks inside the container so Jupyter doesn't block scripts.
# if [[ -f /app/lab_notebooks/malicious_xss.ipynb ]]; then
#   jupyter trust /app/lab_notebooks/malicious_xss.ipynb || true
# fi
# if [[ -f /app/lab_notebooks/safe_demo.ipynb ]]; then
#   jupyter trust /app/lab_notebooks/safe_demo.ipynb || true
# fi

# Launch JupyterLab with server proxy enabled to reach the backend through
# /proxy/9000. Provide JUPYTER_TOKEN/JUPYTER_PASSWORD env vars to override auth.
jupyter lab \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --ServerApp.allow_root=True \
  --ServerApp.allow_remote_access=True \
  --ServerApp.root_dir=/app/lab_notebooks \
  --ServerApp.disable_check_xsrf=True \
  "${AUTH_FLAGS[@]}" &
JUPYTER_PID=$!

wait "$JUPYTER_PID"
