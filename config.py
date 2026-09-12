"""
Shazu Soft Technologies - WhatsApp AI Agent Configuration
Standalone configuration engine reading from .env and environment variables.
"""

import os
import sys

# Attempt to load python-dotenv if available
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(CURRENT_DIR, ".env")

if os.path.exists(env_file):
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        # Fallback manual .env parser
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k not in os.environ:
                        os.environ[k] = v

# Database Configuration (Neon Cloud PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# AI Engine Configuration (Mistral AI)
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
FALLBACK_MODELS = ["open-mistral-7b", "codestral-2508", "mistral-small-latest"]

# Company & Business Profile
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Shazu Soft Technologies")
FOUNDER_NAME = "Vimal Raj"
FOUNDER_PHONE = os.environ.get("FOUNDER_PHONE", "+91 95003 66657")
FOUNDER_EMAIL = os.environ.get("FOUNDER_EMAIL", "contact@shazusoft.com")
LOCATION = "Salem, Tamil Nadu, India"
DEFAULT_TENANT_ID = os.environ.get("DEFAULT_TENANT_ID", "shazusoft")

# Ports
PORT = int(os.environ.get("PORT", 3001))
PYTHON_PORT = int(os.environ.get("PYTHON_PORT", 5005))
PYTHON_WEBHOOK_URL = os.environ.get("PYTHON_WEBHOOK_URL", f"http://127.0.0.1:{PYTHON_PORT}/webhook")
