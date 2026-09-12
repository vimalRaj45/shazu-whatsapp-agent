"""
Shazu Soft - Python Webhook Server for WhatsApp AI Agent
Listens on port 5005 for incoming messages from the Baileys Gateway,
routes them to Mistral AI, and returns the response.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import ai_agent
import db

PORT = 5005

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/webhook":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode("utf-8"))
                phone = data.get("phone", "")
                name = data.get("name", "Client")
                message = data.get("message", "")

                print(f"[WEBHOOK] Received from {phone} ({name}): '{message}'")

                # Generate AI response
                reply = ai_agent.handle_incoming_message(phone, name, message)

                response = {"reply": reply or ""}
                resp_bytes = json.dumps(response, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(resp_bytes)

            except Exception as e:
                print(f"[WEBHOOK] Error processing message: {e}")
                err_bytes = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(err_bytes)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(err_bytes)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/api/leads":
            leads = db.get_leads()
            body = json.dumps(leads, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/stats":
            stats = db.get_stats()
            body = json.dumps(stats, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            stats = db.get_stats()
            self.wfile.write(json.dumps({"status": "ok", "service": "ShazuSoft WhatsApp AI Brain", "neon_db": stats}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Shazu Soft WhatsApp AI Brain with Neon PostgreSQL is running.")

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

def run_server():
    print("[DATABASE] Connecting to Neon Cloud PostgreSQL...")
    db.init_db()
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"[WEBHOOK SERVER] Python AI Brain running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[WEBHOOK SERVER] Shutting down.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
