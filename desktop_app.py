from __future__ import annotations

import argparse
from contextlib import closing
import socket
import threading
import webbrowser

from werkzeug.serving import make_server

from app import create_app
from eng_efficiency.runtime import writable_data_dir


def _find_free_port(host: str) -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(sock.getsockname()[1])


class ServerThread(threading.Thread):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.app = create_app()
        self.server = make_server(host, port, self.app)
        self.context = self.app.app_context()
        self.context.push()

    def run(self) -> None:
        self.server.serve_forever()

    def shutdown(self) -> None:
        self.server.shutdown()
        self.context.pop()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run EngEstimate as a desktop Windows app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="Optional fixed port. Default: auto-select free port.")
    parser.add_argument("--browser", action="store_true", help="Open in an external browser instead of the embedded desktop window.")
    args = parser.parse_args()

    port = args.port or _find_free_port(args.host)
    url = f"http://{args.host}:{port}"
    server = ServerThread(args.host, port)
    server.start()

    try:
        if args.browser:
            webbrowser.open(url)
            while server.is_alive():
                server.join(timeout=0.5)
        else:
            import webview

            data_dir = writable_data_dir()
            data_dir.mkdir(parents=True, exist_ok=True)
            webview.create_window(
                "EngEstimate",
                url,
                width=1440,
                height=960,
                min_size=(1100, 720),
                text_select=True,
            )
            webview.start(private_mode=False)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
