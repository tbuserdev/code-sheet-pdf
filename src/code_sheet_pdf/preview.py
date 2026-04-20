from __future__ import annotations

import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Sequence

from .render import ToolError, build_preview_html, render_pdf


class PreviewServer(ThreadingHTTPServer):
    def __init__(self, server_address, RequestHandlerClass, input_files: Sequence[Path]):
        super().__init__(server_address, RequestHandlerClass)
        self.input_files = list(input_files)


class PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path not in {"/", "/index.html"}:
            self.send_error(404)
            return

        try:
            html = build_preview_html(self.server.input_files)  # type: ignore[attr-defined]
        except ToolError as exc:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(str(exc).encode("utf-8"))
            return

        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def serve_preview(input_files: Sequence[Path], output_file: Path) -> None:
    render_pdf(list(input_files), output_file)

    server = PreviewServer(("127.0.0.1", 0), PreviewHandler, input_files)
    host, port = server.server_address
    url = f"http://{host}:{port}/"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    webbrowser.open(url)
    print(url)

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()
