# 🤖 Shazu Soft - WhatsApp AI Business Automation Platform

A multi-tenant, cloud-native **WhatsApp AI Business Agent** engineered for **Shazu Soft Technologies**. Connects directly to WhatsApp Multi-Device with **zero Green API or third-party subscription fees (₹0/mo)**, powered by **Mistral AI** and backed by **Neon Cloud PostgreSQL**.

---

## 🌟 Key Features

- **⚡ Zero SaaS Gateway Fees**: Connects directly to WhatsApp via `@whiskeysockets/baileys` (runs on your phone's multi-device protocol).
- **🐘 Neon Cloud PostgreSQL**: Real-time cloud persistence for Leads, Conversation history, and Multi-Client WhatsApp accounts.
- **🎨 Tailwind CSS & Bootstrap Icons Light Theme**: Crisp, responsive SaaS dashboard with live CRM leads table and real-time traffic monitor.
- **🗣️ Bilingual AI Consultant**: Speaks natural Tamil, Tanglish, and English, trained on Shazu Soft's 3 Core Pillars (Custom Software, AI Agents, Scalable SaaS).
- **⏸️ Human Takeover Support**: Send `#stop` in any chat to pause AI for 24 hours; send `#start` to resume.
- **🚀 1-Click Render.com Deployment**: Containerized with Docker and ready to deploy 24/7 in the cloud.

---

## 📁 Repository Structure

```text
whatsapp_agent/
├── .env                       # Environment credentials (Neon DB, Mistral Key)
├── .env.example               # Public template
├── Dockerfile                 # Multi-runtime (Node.js 20 + Python 3.11)
├── render.yaml                # 1-Click Render.com Blueprint
├── requirements.txt           # Python dependencies
├── config.py                  # Standalone configuration manager
├── db.py                      # Multi-tenant Neon PostgreSQL ORM / Driver
├── ai_agent.py                # Mistral AI conversational intelligence engine
├── webhook_server.py          # Python HTTP server for AI & DB API endpoints
├── run_system.py              # Unified daemon launcher
└── gateway/
    ├── index.js               # Baileys WhatsApp Gateway & Express REST API
    ├── dashboard.html         # Tailwind CSS & Bootstrap Icons Light UI
    ├── package.json           # Node.js dependencies
    └── auth_info/             # Multi-device session keys (auto-persisted)
```

---

## 🚀 Local Quickstart

### 1. Install Dependencies
```bash
# Python
pip install -r requirements.txt

# Node.js Gateway
cd gateway && npm install && cd ..
```

### 2. Configure Environment
Your `.env` is already pre-configured with Neon PostgreSQL and Mistral AI keys.

### 3. Start the System
```bash
python run_system.py
```
Open **`http://localhost:3001/qr`** in your browser to view your live Tailwind dashboard and scan the QR code!

---

## ☁️ 1-Click Deploy on Render.com

1. Push this folder to a new GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of WhatsApp AI Agent"
   git branch -M main
   git remote add origin https://github.com/YOUR_USER/shazu-whatsapp-agent.git
   git push -u origin main
   ```
2. In [Render Dashboard](https://dashboard.render.com), click **New +** &rarr; **Blueprint** (or **Web Service**).
3. Select your repository.
4. Render will auto-detect `render.yaml` and `Dockerfile`.
5. Once deployed, open `https://your-service.onrender.com/qr` to link WhatsApp 24/7!
