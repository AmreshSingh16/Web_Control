"""
block_server.py
A tiny local web server that serves a friendly "this website is blocked"
page. Blocked domains are redirected (via the hosts file) to 127.0.0.1,
so their requests land here instead of a dead connection.

Only handles plain HTTP (port 80). Most modern sites force HTTPS, so
those requests will typically show the browser's own security warning
instead of this page — that's a limitation of hosts-file blocking, not
something fixable without a full local proxy + trusted certificate.
"""

import http.server
import threading

PORT = 80
BIND_ADDR = "127.0.0.1"

BLOCKED_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Site Blocked</title>
<style>
  html, body {{
    height: 100%;
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #1a1a1a;
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #f2f2f2;
  }}
  .card {{
    text-align: center;
    padding: 48px 56px;
    background: #242424;
    border-radius: 16px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    max-width: 420px;
  }}
  .stop-sign {{
    width: 96px;
    height: 96px;
    margin: 0 auto 20px auto;
  }}
  h1 {{
    font-size: 22px;
    margin: 0 0 8px 0;
    color: #ff4b4b;
  }}
  .domain {{
    font-size: 17px;
    font-weight: 600;
    color: #ffffff;
    word-break: break-all;
    margin-bottom: 14px;
  }}
  p {{
    font-size: 14px;
    color: #b5b5b5;
    line-height: 1.5;
    margin: 0;
  }}
</style>
</head>
<body>
  <div class="card">
    <svg class="stop-sign" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <polygon points="29,4 71,4 96,29 96,71 71,96 29,96 4,71 4,29"
               fill="#ff4b4b" stroke="#ffffff" stroke-width="3"/>
      <rect x="24" y="44" width="52" height="12" rx="2" fill="#ffffff"/>
    </svg>
    <h1>Access Blocked</h1>
    <div class="domain">{domain}</div>
    <p>This website has been blocked. You are not allowed to access it on this device.</p>
  </div>
</body>
</html>
"""


class BlockPageHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self._serve()

    def do_POST(self):
        self._serve()

    def _serve(self):
        domain = self.headers.get("Host", "this site").split(":")[0]
        body = BLOCKED_PAGE_TEMPLATE.format(domain=domain).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Silence default request logging to keep the console clean
        pass


def start_block_server():
    """
    Start the block page server in a background thread.
    Returns the HTTPServer instance on success, or None if port 80
    couldn't be bound (e.g. already in use by IIS, Skype, another
    local server, etc.) — the app should keep working either way,
    it just won't show the friendly page for HTTP requests.
    """
    try:
        server = http.server.HTTPServer((BIND_ADDR, PORT), BlockPageHandler)
    except OSError:
        return None

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server