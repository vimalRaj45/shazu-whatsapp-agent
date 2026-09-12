"""
Shazu Soft Technologies - 24/7 WhatsApp AI Business Agent Engine
Powered by Mistral AI (Multi-model fallback) & Baileys Gateway
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import time
import re
from typing import Dict, List, Optional
import urllib.request
import urllib.error

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import config
import db

# Memory cache for active conversations: { phone_number: [ {"role": "user"/"assistant", "content": "..."} ] }
CONVERSATION_MEMORY: Dict[str, List[Dict[str, str]]] = {}
# Human takeover mute tracker: { phone_number: mute_until_timestamp }
HUMAN_TAKEOVER_MUTES: Dict[str, float] = {}

SYSTEM_PROMPT = """You are the official 24/7 Senior AI Technical Consultant for Shazu Soft Technologies (Salem, Tamil Nadu).
Our Founder & Tech Lead is Vimal Raj (Phone: +91 95003 66657, Email: contact@shazusoft.com, Website: software.html).

YOUR MISSION:
Help prospective clients, business owners, and founders who message us on WhatsApp understand how Shazu Soft can build their software or automate their operations. Be helpful, concise, friendly, and consultative. Never write walls of text—keep WhatsApp responses under 3-4 short paragraphs or punchy bullet points.

SHAZU SOFT'S 3 CORE PILLARS (Everything we do fits into these 3):
1. PILLAR 1: CUSTOM SOFTWARE ENGINEERING
   - Bespoke web apps (React, Next.js, Node.js, PostgreSQL), internal operations portals, ERPs, CRM systems, and cross-platform mobile apps (Flutter, iOS & Android).
   - 100% custom code ownership, no vendor lock-in. Replaces messy manual spreadsheets.

2. PILLAR 2: AI AGENTS FOR BUSINESS AUTOMATION
   - 24/7 bilingual (Tamil & English) conversational WhatsApp & Web AI agents.
   - Handles customer inquiries, qualifies leads, books appointments, and triggers Playwright/Cron background tasks without human staff intervention.

3. PILLAR 3: SCALABLE SAAS PLATFORMS
   - Multi-tenant cloud SaaS software built from scratch.
   - Includes tenant data isolation, automated Stripe/Razorpay subscription billing engines, and self-service customer portals.

LANGUAGE & TONE RULES:
- If the user writes in English, reply in crisp, professional, friendly English.
- If the user writes in Tamil or Tanglish (e.g. "Vanakkam", "enaku oru clinic software venum", "pricing evlo bro", "epdi work aagum"), reply in natural, friendly, professional Tanglish/Tamil.
- Ask 1 clarifying question at the end to understand their business type or feature requirements.
- Invite them to schedule a free 15-minute scoping call with our engineering team or visit our live portfolio.
- DO NOT make up random false prices. Mention that we deliver in transparent 2-week agile sprints and invite them for a quick quote based on their exact scope.
"""

def call_mistral(messages: List[Dict[str, str]]) -> str:
    """Call Mistral AI with multi-model fallback."""
    headers = {
        "Authorization": f"Bearer {config.MISTRAL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload_base = {
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 450
    }

    last_err = None
    models = getattr(config, "FALLBACK_MODELS", ["open-mistral-7b", "codestral-2508"])
    for model in models:
        payload = dict(payload_base)
        payload["model"] = model
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request("https://api.mistral.ai/v1/chat/completions", data=data, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_body = resp.read().decode("utf-8")
                res_json = json.loads(res_body)
                content = res_json["choices"][0]["message"]["content"].strip()
                if content:
                    return content
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            last_err = f"Model {model} HTTP {e.code}: {err_body}"
            if e.code == 429:
                time.sleep(1)
                continue
        except Exception as e:
            last_err = f"Model {model} Error: {str(e)}"
            continue

    return (
        "Hello! Thank you for contacting Shazu Soft Technologies. "
        "Our senior development team in Salem has received your message and will review your requirements shortly. "
        "You can also reach our tech lead directly at +91 95003 66657."
    )

def handle_incoming_message(sender_phone: str, sender_name: str, message_text: str) -> Optional[str]:
    """
    Process incoming WhatsApp message:
    - Check Human Takeover commands (#stop, #start)
    - Check if muted
    - Maintain conversation history
    - Generate Mistral response
    - Log lead to CRM
    """
    clean_text = (message_text or "").strip()
    clean_phone = re.sub(r"[^0-9]", "", sender_phone)
    now = time.time()

    # 1. Human Takeover commands
    lower_text = clean_text.lower()
    if lower_text in ["#stop", "#pause", "#mute", "#human"]:
        HUMAN_TAKEOVER_MUTES[clean_phone] = now + (24 * 3600)  # Mute for 24h
        return "AI Agent paused for this chat for 24 hours. A human specialist from Shazu Soft will continue the conversation with you."

    if lower_text in ["#start", "#resume", "#unmute", "#ai"]:
        if clean_phone in HUMAN_TAKEOVER_MUTES:
            del HUMAN_TAKEOVER_MUTES[clean_phone]
        return "AI Agent reactivated. How can Shazu Soft help your business today?"

    # Check if currently muted
    if clean_phone in HUMAN_TAKEOVER_MUTES:
        if now < HUMAN_TAKEOVER_MUTES[clean_phone]:
            print(f"[AI AGENT] Chat {clean_phone} is currently MUTED (Human takeover active). Ignoring message.")
            return None
        else:
            del HUMAN_TAKEOVER_MUTES[clean_phone]

    # 2. Retrieve conversation history (from Neon DB or fallback memory)
    history = db.get_chat_history(clean_phone, limit=8)
    if not history and clean_phone in CONVERSATION_MEMORY:
        history = list(CONVERSATION_MEMORY[clean_phone])
    
    history.append({"role": "user", "content": clean_text})
    if len(history) > 8:
        history = history[-8:]
    CONVERSATION_MEMORY[clean_phone] = history

    # 3. Build Mistral messages payload with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)

    # 4. Generate AI response
    print(f"[AI AGENT] Generating response for {clean_phone} ({sender_name}): '{clean_text}'")
    ai_reply = call_mistral(messages)

    # 5. Save assistant response to memory & Neon PostgreSQL
    history.append({"role": "assistant", "content": ai_reply})
    CONVERSATION_MEMORY[clean_phone] = history

    # Save conversation turns to Neon PostgreSQL
    chat_jid = f"{clean_phone}@s.whatsapp.net"
    db.save_message(chat_jid, clean_phone, sender_name, "user", clean_text)
    db.save_message(chat_jid, clean_phone, "Shazu AI Agent", "assistant", ai_reply)

    # 6. Save Lead to Neon PostgreSQL Cloud DB
    db.save_lead(clean_phone, sender_name, clean_text, ai_reply)

    # 7. Also update local enriched_leads.json if present
    log_lead_to_crm(clean_phone, sender_name, clean_text, ai_reply)

    return ai_reply

def log_lead_to_crm(phone: str, name: str, latest_inquiry: str, last_reply: str):
    """Auto-log inbound WhatsApp prospect to enriched_leads.json (local fallback)."""
    try:
        leads_path = os.path.join(CURRENT_DIR, "enriched_leads.json")
        if not os.path.exists(leads_path):
            parent = os.path.dirname(CURRENT_DIR)
            alt_path = os.path.join(parent, "enriched_leads.json")
            if os.path.exists(alt_path):
                leads_path = alt_path

        leads_data = []
        if os.path.exists(leads_path):
            with open(leads_path, "r", encoding="utf-8") as f:
                leads_data = json.load(f)

        # Check if lead already exists
        existing_lead = None
        for item in leads_data:
            lead_phone = re.sub(r"[^0-9]", "", str(item.get("phone") or ""))
            if lead_phone and (lead_phone == phone or lead_phone.endswith(phone[-10:]) or phone.endswith(lead_phone[-10:])):
                existing_lead = item
                break

        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        if existing_lead:
            existing_lead["status"] = "In Conversation"
            existing_lead["whatsapp_last_inquiry"] = latest_inquiry
            existing_lead["whatsapp_last_active"] = now_str
            existing_lead["score"] = max(existing_lead.get("score", 50), 85)
        else:
            new_lead = {
                "id": f"wa_{phone[-10:]}",
                "name": name or f"WhatsApp Lead ({phone[-4:]})",
                "phone": f"+{phone}",
                "category": "Inbound WhatsApp Inquiry",
                "address": "Inbound WhatsApp Prospect",
                "priority": "High Priority",
                "score": 90,
                "status": "In Conversation",
                "whatsapp_last_inquiry": latest_inquiry,
                "whatsapp_last_active": now_str,
                "primary_offering": "24/7 AI Agent / Custom Software",
                "recommended_services": [
                    "Pillar 1: Custom Software Engineering",
                    "Pillar 2: AI Agents for Business Automation",
                    "Pillar 3: Scalable SaaS Platforms"
                ]
            }
            leads_data.insert(0, new_lead)

        with open(leads_path, "w", encoding="utf-8") as f:
            json.dump(leads_data, f, indent=2, ensure_ascii=False)

        print(f"[AI AGENT] Successfully logged lead {phone} to CRM ({leads_path})")

    except Exception as e:
        print(f"[AI AGENT] Warning: Failed to sync lead to CRM: {e}")

if __name__ == "__main__":
    print("Testing AI Agent locally with test inquiry...")
    test_reply = handle_incoming_message("919500366657", "Vimal Raj", "Hi, enaku oru hospital management software and WhatsApp bot venum. What are your 3 pillars?")
    print("\n--- AI AGENT REPLY ---")
    print(test_reply)
