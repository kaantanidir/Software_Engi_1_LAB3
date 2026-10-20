"""Run the local SmartBrew browser application: python app.py --port 8765."""

import argparse
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import mimetypes
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
# The target directory supports this desktop's bundled Python; normal users use a venv.
if (ROOT / ".packages").is_dir():
    sys.path.insert(0, str(ROOT / ".packages"))

import qrcode
from qrcode.image.svg import SvgPathImage
from smartbrew.service import RuleError, Store
from smartbrew.assistant import LocalAssistant


class Handler(BaseHTTPRequestHandler):
    """HTTP adapter for JSON services, static UI and capability receipt pages."""

    def token(self):
        """Purpose: read HttpOnly session cookie. Inputs: request headers. Returns: session string."""
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except Exception:
            return ""
        return cookies["session"].value if "session" in cookies else ""

    def respond(self, content, status=200, mime="application/json; charset=utf-8", cookie=None):
        """Purpose: write a secure response. Inputs: payload/status/MIME/optional cookie. Returns: None."""
        if not isinstance(content, bytes):
            content = json.dumps(content, ensure_ascii=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; style-src-attr 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'")
        if cookie is not None:
            self.send_header("Set-Cookie", "session=" + cookie + "; HttpOnly; SameSite=Strict; Path=/; Max-Age=" + ("28800" if cookie else "0"))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        """Purpose: route read requests. Inputs: HTTP path/session. Returns: response to client."""
        try:
            self.get_route()
        except RuleError as error:
            self.respond({"error": str(error)}, error.status)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def get_route(self):
        """Purpose: resolve static/API/receipt resources. Inputs: current request. Returns: None."""
        path = unquote(urlparse(self.path).path)
        store = self.server.store
        if path == "/api/state":
            self.respond(store.state(self.token()))
        elif path == "/api/recommendations":
            self.respond(store.recommendations(self.token()))
        elif path == "/api/assistant/status":
            self.respond(self.server.assistant.status())
        elif path == "/api/diagnostics":
            self.respond(store.diagnostics(self.token()))
        elif path.startswith("/receipt/"):
            parts = path.strip("/").split("/")
            if len(parts) not in (2, 3) or (len(parts) == 3 and parts[2] != "qr.svg"):
                raise RuleError("Receipt not found.", 404)
            order = store.receipt(parts[1])
            if len(parts) == 3:
                config = order["recipe"]["config"]
                text = f"SmartBrew AI | Receipt #{order['id']}\n{order['created']}\n{order['recipe']['name']}\n{config['milk']} / {config['strength']} / {config['temperature']} C\nSyrup shots: {config['syrup']} | Extra espresso: {config['extra']}\nSubtotal: SEK {order['amount']/100:.2f}\nDiscount: SEK {order['discount']/100:.2f}\nPaid: SEK {order['paid']/100:.2f}\nPayment simulator: {order['method']}"
                qr = qrcode.make(text, image_factory=SvgPathImage, box_size=6, border=4)
                output = BytesIO()
                qr.save(output)
                self.respond(output.getvalue(), mime="image/svg+xml")
            else:
                self.respond((ROOT / "web" / "receipt.html").read_bytes(), mime="text/html; charset=utf-8")
        elif path.startswith("/api/receipt/"):
            self.respond({"order": store.receipt(path.rsplit("/", 1)[-1])})
        else:
            base = (ROOT / "web").resolve()
            target = (base / ("index.html" if path == "/" else path.lstrip("/"))).resolve()
            if not target.is_relative_to(base) or not target.is_file():
                raise RuleError("Not found.", 404)
            self.respond(target.read_bytes(), mime=mimetypes.guess_type(target)[0] or "application/octet-stream")

    def do_POST(self):
        """Purpose: validate/rout mutation requests. Inputs: JSON HTTP request. Returns: response to client."""
        try:
            host = self.headers.get("Host", "")
            if host.rsplit(":", 1)[0] not in ("127.0.0.1", "localhost"):
                raise RuleError("Localhost access only.", 403)
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + host:
                raise RuleError("Cross-origin mutation denied.", 403)
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise RuleError("Send JSON.", 415)
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16384:
                raise RuleError("Request body must be between 1 and 16384 bytes.", 413)
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise RuleError("Expected a JSON object.")
            path = urlparse(self.path).path
            store = self.server.store
            token = self.token()
            cookie = None
            if path.startswith("/api/auth/"):
                result, cookie = store.auth(path.rsplit("/", 1)[-1], data, token)
            elif path == "/api/quote":
                with store.connection() as db:
                    result = store.quote(db, data)
            elif path.startswith("/api/recipes/"):
                result = store.recipes(token, path.rsplit("/", 1)[-1], data)
            elif path == "/api/checkout":
                result = store.checkout(token, data)
            elif path == "/api/assistant":
                result = self.server.assistant.suggest(token, data)
            elif path == "/api/email-receipt":
                result = store.email_receipt(token, data)
            elif path.startswith("/api/admin/"):
                result = store.admin(token, path.rsplit("/", 1)[-1], data)
            else:
                raise RuleError("Unknown endpoint.", 404)
            self.respond(result, cookie=cookie)
        except RuleError as error:
            self.respond({"error": str(error)}, error.status)
        except (ValueError, TypeError, AttributeError):
            self.respond({"error": "Invalid JSON or field type."}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    """Purpose: launch the local server. Inputs: CLI --port/--database. Returns: None until stopped."""
    parser = argparse.ArgumentParser(description="SmartBrew local prototype")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--database", type=Path, default=ROOT / "data" / "smartbrew.sqlite3")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434", help="Optional local Ollama API (loopback only)")
    parser.add_argument("--model", default="qwen3:4b", help="Installed local drink-assistant model")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.store = Store(args.database)
    server.assistant = LocalAssistant(server.store, args.ollama_url, args.model)
    print(f"SmartBrew AI ready at http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
