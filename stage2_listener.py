#!/usr/bin/env python3
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys


class LeakHandler(BaseHTTPRequestHandler):
    server_version = "Stage2Leak/0.1"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_POST(self):  # noqa: N802
        if self.path != "/leak":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length > 0 else b""

        print("--- inbound leak ---")
        print(f"Path: {self.path}")
        print("Headers:")
        for k, v in self.headers.items():
            print(f"  {k}: {v}")
        print(f"Body ({len(body)} bytes):")
        print(body.decode("utf-8", errors="replace"))
        print("--------------------")
        sys.stdout.flush()

        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(b"ok\n")

    def do_GET(self):  # noqa: N802
        if self.path != "/leak":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(b"listener up\n")

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def log_message(self, fmt, *args):  # noqa: A003
        return


parser = argparse.ArgumentParser(description="Tiny HTTP listener for POST /leak")
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--port", type=int, default=8080)
args = parser.parse_args()

server = (args.host, args.port)
httpd = HTTPServer(server, LeakHandler)
print(f"Listening on http://{args.host}:{args.port}/leak (POST only)")
httpd.serve_forever()
