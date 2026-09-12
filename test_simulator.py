"""
Shazu Soft - Interactive WhatsApp AI Agent Simulator
Test conversations in terminal without needing a second phone!
"""

import urllib.request
import json
import sys

URL = "http://localhost:5005/webhook"

def test_chat():
    print("=" * 60)
    print("   SHAZU SOFT WHATSAPP AI AGENT - INTERACTIVE TESTER")
    print("=" * 60)
    print("Simulating inbound WhatsApp messages directly to Python AI Brain.")
    print("Type 'exit' to quit.\n")

    phone = "919876543210"
    name = "Salem Client"

    while True:
        try:
            msg = input("\nYou (Customer WhatsApp Message): ").strip()
            if not msg:
                continue
            if msg.lower() in ["exit", "quit"]:
                break

            payload = json.dumps({
                "phone": phone,
                "name": name,
                "message": msg
            }).encode("utf-8")

            req = urllib.request.Request(
                URL, 
                data=payload, 
                headers={"Content-Type": "application/json", "Connection": "close"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data.get("reply", "")
                print(f"\n[AI Agent WhatsApp Reply]:\n{reply}")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting simulator.")
            break
        except Exception as e:
            print(f"\nError contacting agent: {e}")

if __name__ == "__main__":
    test_chat()
