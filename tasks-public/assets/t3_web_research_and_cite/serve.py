"""Serve the local sandboxed news site for the research-and-cite task."""

from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).parent / "articles"
ARTICLES = {path.stem: path for path in ROOT.glob("*.html") if path.is_file()}


def article_for_request_path(request_path: str) -> Path | None:
    path = unquote(urlsplit(request_path).path)
    if not path.startswith("/article/"):
        return None
    slug = path.removeprefix("/article/")
    return ARTICLES.get(slug)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = unquote(urlsplit(self.path).path)
        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            return
        if path == "/" or path == "/index":
            self._index()
            return
        if path.startswith("/article/"):
            article = article_for_request_path(self.path)
            if article is not None:
                self._html(article.read_bytes())
                return
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"not found")

    def _index(self) -> None:
        items = []
        for slug in sorted(ARTICLES):
            items.append(f'<li><a href="/article/{slug}">{slug}</a></li>')
        body = (
            "<!doctype html><html><body>"
            "<h1>Sandboxed News Index</h1><ul>"
            + "".join(items)
            + "</ul></body></html>"
        ).encode("utf-8")
        self._html(body)

    def _html(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        pass


def main() -> None:
    port = int(os.environ.get("PORT", "0"))
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"sandbox news site listening on http://127.0.0.1:{server.server_address[1]}")
    server.serve_forever()


if __name__ == "__main__":
    main()
