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

from urllib.parse import urlparse, parse_qs
import re
import time

class WebhookHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            data = {}

        if path in ("/webhook", "/api/test-chat", "/api/simulate"):
            try:
                phone = data.get("phone", "")
                name = data.get("name", "Client")
                message = data.get("message", "")
                tenant_id = data.get("tenant_id") or "shazusoft"

                print(f"[WEBHOOK] Received for tenant '{tenant_id}' from {phone} ({name}): '{message}'")

                # Generate AI response tailored to this business tenant
                reply = ai_agent.handle_incoming_message(phone, name, message, tenant_id=tenant_id)

                self._send_json(200, {"reply": reply or "", "tenant_id": tenant_id})
            except Exception as e:
                print(f"[WEBHOOK] Error processing message: {e}")
                self._send_json(500, {"error": str(e)})

        elif path == "/api/tenants":
            try:
                name = (data.get("name") or "").strip()
                if not name:
                    return self._send_json(400, {"error": "Business name is required"})

                tenant_id = data.get("tenant_id") or re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
                tenant_id = tenant_id[:40].strip('_')
                if not tenant_id:
                    tenant_id = f"biz_{int(time.time())}"

                phone = data.get("phone") or ""
                category = data.get("category") or "General Business"
                knowledge_base = data.get("knowledge_base") or f"Official WhatsApp AI agent for {name}."
                website_url = data.get("website_url") or "https://shazusofttechnologies.org/software"

                success = db.create_tenant(
                    tenant_id=tenant_id,
                    name=name,
                    phone=phone,
                    category=category,
                    knowledge_base=knowledge_base,
                    website_url=website_url
                )

                if success:
                    tenant = db.get_tenant(tenant_id)
                    self._send_json(201, {"success": True, "tenant": tenant, "message": f"AI Agent for '{name}' successfully activated!"})
                else:
                    self._send_json(500, {"error": "Failed to register tenant in database"})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif path == "/api/tenants/knowledge":
            try:
                tenant_id = data.get("tenant_id") or "shazusoft"
                knowledge_base = data.get("knowledge_base", "")
                success = db.update_tenant_knowledge(tenant_id, knowledge_base)
                if success:
                    self._send_json(200, {"success": True, "message": "Knowledge base updated successfully"})
                else:
                    self._send_json(500, {"error": "Failed to update knowledge base"})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tenants/knowledge":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                tenant_id = data.get("tenant_id") or "shazusoft"
                knowledge_base = data.get("knowledge_base", "")
                success = db.update_tenant_knowledge(tenant_id, knowledge_base)
                if success:
                    self._send_json(200, {"success": True, "message": "Knowledge base updated successfully"})
                else:
                    self._send_json(500, {"error": "Failed to update knowledge base"})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        tenant_id = query.get("tenant_id", ["shazusoft"])[0]

        if path == "/api/tenants":
            tenants = db.get_all_tenants()
            self._send_json(200, tenants)

        elif path == "/api/tenants/details":
            tenant = db.get_tenant(tenant_id)
            if tenant:
                self._send_json(200, tenant)
            else:
                self._send_json(404, {"error": f"Tenant '{tenant_id}' not found"})

        elif path == "/api/leads":
            limit = int(query.get("limit", [50])[0])
            leads = db.get_leads(tenant_id=tenant_id, limit=limit)
            self._send_json(200, leads)

        elif path == "/api/stats":
            stats = db.get_stats(tenant_id=tenant_id)
            self._send_json(200, stats)

        elif path == "/health":
            stats = db.get_stats(tenant_id="shazusoft")
            self._send_json(200, {"status": "ok", "service": "ShazuSoft WhatsApp AI Brain", "neon_db": stats})

        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Shazu Soft WhatsApp AI Brain with Multi-Tenant Neon PostgreSQL is running.")

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
