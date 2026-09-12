"""
Shazu Soft - Unified Launcher for WhatsApp AI Agent
Starts both the Python AI Brain and the Node.js Baileys Gateway in parallel.
"""

import subprocess
import sys
import os
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GATEWAY_DIR = os.path.join(CURRENT_DIR, "gateway")

def main():
    print("=" * 65)
    print("      SHAZU SOFT TECHNOLOGIES - 24/7 WHATSAPP AI AGENT")
    print("=" * 65)
    print("Initializing services...")

    # 1. Start Python Webhook Server
    py_server_path = os.path.join(CURRENT_DIR, "webhook_server.py")
    py_env = os.environ.copy()
    py_env["PYTHONIOENCODING"] = "utf-8"
    py_proc = subprocess.Popen([sys.executable, py_server_path], cwd=CURRENT_DIR, env=py_env)
    print("[1/2] Python AI Brain Server started on port 5005")

    time.sleep(1)

    # 2. Start Node.js Baileys Gateway
    node_script_path = os.path.join(GATEWAY_DIR, "index.js")
    node_proc = subprocess.Popen(["node", node_script_path], cwd=GATEWAY_DIR)
    print("[2/2] Node.js Baileys WhatsApp Gateway started on port 3001")

    print("\n" + "-" * 65)
    print(">>> HOW TO CONNECT YOUR WHATSAPP:")
    print("1. Open your browser to view the QR Code:")
    print("   -> http://localhost:3001/qr")
    print("2. Open WhatsApp on your phone -> Settings -> Linked Devices -> Link a Device")
    print("3. Point your camera at the QR code on your screen!")
    print("-" * 65 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping WhatsApp Agent services...")
        py_proc.terminate()
        node_proc.terminate()
        print("All services stopped.")

if __name__ == "__main__":
    main()
