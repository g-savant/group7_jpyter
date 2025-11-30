import asyncio
import json
import os
import shlex

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket


class HiHandler(tornado.web.RequestHandler):
    def get(self) -> None:
        self.set_header("Content-Type", "text/plain")
        self.write("Hi")


class CommandWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin: str) -> bool:
        return True

    async def on_message(self, message: str) -> None:
        command = message.strip()
        if not command:
            await self.write_message(json.dumps({"error": "Empty command"}))
            return
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await proc.communicate()
        result = {
            "command": command,
            "argv": shlex.split(command),
            "returncode": proc.returncode,
            "stdout": stdout_b.decode("utf-8", errors="replace"),
            "stderr": stderr_b.decode("utf-8", errors="replace"),
        }
        await self.write_message(json.dumps(result))

    async def _run_command(self, command: str) -> dict:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await proc.communicate()
        return {
            "command": command,
            "argv": shlex.split(command),
            "returncode": proc.returncode,
            "stdout": stdout_b.decode("utf-8", errors="replace"),
            "stderr": stderr_b.decode("utf-8", errors="replace"),
        }

    async def _send_error(self, message: str) -> None:
        await self.write_message(json.dumps({"error": message}))


def make_app() -> tornado.web.Application:
    return tornado.web.Application(
        [
            (r"/hi", HiHandler),
            (r"/ws", CommandWebSocket),
        ]
    )


def main(host: str = "0.0.0.0", port: int = 9000) -> None:
    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port, address=host)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    listen_host = os.environ.get("BACKEND_HOST", "0.0.0.0")
    listen_port = int(os.environ.get("BACKEND_PORT", "9000"))
    main(listen_host, listen_port)
