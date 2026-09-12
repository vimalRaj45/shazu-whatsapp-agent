"""
Shazu Soft Technologies - Multi-Tenant Neon PostgreSQL Database Engine
Powers 24/7 cloud persistence for Leads, Chat turns, Activity logs, and Multi-Client WhatsApp Instances.
"""

import os
import sys
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import config

def get_connection():
    """Create a thread-safe connection to Neon Cloud PostgreSQL."""
    return psycopg2.connect(config.DATABASE_URL, sslmode="require")

def init_db():
    """Auto-migrate all tables and seed the default Shazu Soft tenant."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1. Tenants Table (Multi-Client SaaS Isolation)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(50),
                category VARCHAR(100) DEFAULT 'Software & AI',
                knowledge_base TEXT,
                custom_prompt TEXT,
                website_url VARCHAR(255) DEFAULT 'https://shazusofttechnologies.org/software',
                viral_footer_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Alter table in case it was created earlier without new columns
        cur.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'Software & AI';")
        cur.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS knowledge_base TEXT;")
        cur.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS website_url VARCHAR(255) DEFAULT 'https://shazusofttechnologies.org/software';")
        cur.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS viral_footer_enabled BOOLEAN DEFAULT TRUE;")

        # 2. WhatsApp Instances Table (Multiple Phone Connections)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_instances (
                id VARCHAR(64) PRIMARY KEY,
                tenant_id VARCHAR(64) REFERENCES tenants(id) ON DELETE CASCADE,
                phone VARCHAR(50),
                status VARCHAR(50) DEFAULT 'initializing',
                qr_code TEXT,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # 3. CRM Leads Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id VARCHAR(64) PRIMARY KEY,
                tenant_id VARCHAR(64) REFERENCES tenants(id) ON DELETE CASCADE,
                name VARCHAR(255),
                phone VARCHAR(50) NOT NULL,
                category VARCHAR(100) DEFAULT 'Inbound WhatsApp Inquiry',
                priority VARCHAR(50) DEFAULT 'High Priority',
                score INTEGER DEFAULT 90,
                status VARCHAR(50) DEFAULT 'In Conversation',
                whatsapp_last_inquiry TEXT,
                whatsapp_last_reply TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # 4. Message History Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id BIGSERIAL PRIMARY KEY,
                tenant_id VARCHAR(64) REFERENCES tenants(id) ON DELETE CASCADE,
                chat_jid VARCHAR(100),
                sender_phone VARCHAR(50),
                sender_name VARCHAR(255),
                role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
                message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # 5. Activity Logs Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id BIGSERIAL PRIMARY KEY,
                tenant_id VARCHAR(64) REFERENCES tenants(id) ON DELETE CASCADE,
                log_type VARCHAR(50) NOT NULL,
                message TEXT,
                details TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Seed Default Shazu Soft Tenant if it doesn't exist
        cur.execute("""
            INSERT INTO tenants (id, name, phone, category, knowledge_base, custom_prompt, website_url, viral_footer_enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                website_url = 'https://shazusofttechnologies.org/software',
                name = EXCLUDED.name;
        """, (
            config.DEFAULT_TENANT_ID,
            config.COMPANY_NAME,
            config.FOUNDER_PHONE,
            "Custom Software & AI Solutions",
            "Shazu Soft Technologies builds custom software, AI agents for business automation, and scalable SaaS platforms. Founder: Vimal Raj (+91 95003 66657, contact@shazusoft.com). Website: https://shazusofttechnologies.org/software",
            "Official 24/7 AI Business Consultant for Shazu Soft Technologies.",
            "https://shazusofttechnologies.org/software",
            True
        ))

        # Seed Primary WhatsApp Instance
        cur.execute("""
            INSERT INTO whatsapp_instances (id, tenant_id, phone, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (
            f"inst_{config.DEFAULT_TENANT_ID}",
            config.DEFAULT_TENANT_ID,
            "918807099288",
            "connected"
        ))

        conn.commit()
        cur.close()
        print("[DATABASE] Neon PostgreSQL connected & schema migrated successfully!")
        return True
    except Exception as e:
        print(f"[DATABASE ERROR] Could not initialize database: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def save_lead(phone: str, name: str, inquiry: str, reply: str, tenant_id: str = "shazusoft", score: int = 90, status: str = "In Conversation") -> bool:
    """Insert or update a lead in Neon PostgreSQL."""
    clean_phone = "".join(c for c in phone if c.isdigit())
    lead_id = f"wa_{clean_phone[-10:]}" if len(clean_phone) >= 10 else f"wa_{clean_phone}"
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO leads (id, tenant_id, name, phone, category, priority, score, status, whatsapp_last_inquiry, whatsapp_last_reply, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                whatsapp_last_inquiry = EXCLUDED.whatsapp_last_inquiry,
                whatsapp_last_reply = EXCLUDED.whatsapp_last_reply,
                status = EXCLUDED.status,
                score = GREATEST(leads.score, EXCLUDED.score),
                updated_at = NOW();
        """, (
            lead_id,
            tenant_id,
            name or f"WhatsApp Lead ({clean_phone[-4:]})",
            f"+{clean_phone}",
            "Inbound WhatsApp Inquiry",
            "High Priority",
            score,
            status,
            inquiry,
            reply
        ))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"[DATABASE ERROR] Failed saving lead: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_leads(tenant_id: str = "shazusoft", limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve all leads for the given tenant."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, name, phone, category, priority, score, status, whatsapp_last_inquiry, whatsapp_last_reply,
                   TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at_formatted
            FROM leads
            WHERE tenant_id = %s
            ORDER BY updated_at DESC
            LIMIT %s;
        """, (tenant_id, limit))
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DATABASE ERROR] Failed fetching leads: {e}")
        return []
    finally:
        if conn:
            conn.close()

def save_message(chat_jid: str, phone: str, name: str, role: str, text: str, tenant_id: str = "shazusoft") -> bool:
    """Save a conversation turn to Neon PostgreSQL."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO messages (tenant_id, chat_jid, sender_phone, sender_name, role, message)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (tenant_id, chat_jid, phone, name, role, text))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"[DATABASE ERROR] Failed saving message: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_chat_history(phone: str, tenant_id: str = "shazusoft", limit: int = 8) -> List[Dict[str, str]]:
    """Fetch recent chat history turns for Mistral AI context window."""
    clean_phone = "".join(c for c in phone if c.isdigit())
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT role, message as content
            FROM messages
            WHERE tenant_id = %s AND sender_phone LIKE %s
            ORDER BY created_at DESC
            LIMIT %s;
        """, (tenant_id, f"%{clean_phone[-10:]}%" if len(clean_phone) >= 10 else f"%{clean_phone}%", limit))
        rows = cur.fetchall()
        cur.close()
        # Return in chronological order
        return [dict(r) for r in reversed(rows)]
    except Exception as e:
        print(f"[DATABASE ERROR] Failed fetching history: {e}")
        return []
    finally:
        if conn:
            conn.close()

def log_activity(log_type: str, message: str, details: Optional[str] = None, tenant_id: str = "shazusoft") -> bool:
    """Store persistent activity logs in Neon PostgreSQL."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO activity_logs (tenant_id, log_type, message, details)
            VALUES (%s, %s, %s, %s);
        """, (tenant_id, log_type, message, details))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_stats(tenant_id: str = "shazusoft") -> Dict[str, Any]:
    """Calculate key SaaS metrics from Neon PostgreSQL."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM leads WHERE tenant_id = %s;", (tenant_id,))
        total_leads = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM messages WHERE tenant_id = %s;", (tenant_id,))
        total_messages = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT sender_phone) FROM messages WHERE tenant_id = %s;", (tenant_id,))
        active_conversations = cur.fetchone()[0]

        cur.close()
        return {
            "total_leads": total_leads,
            "total_messages": total_messages,
            "active_conversations": active_conversations,
            "db_status": "connected",
            "provider": "Neon Cloud PostgreSQL"
        }
    except Exception as e:
        print(f"[DATABASE ERROR] Failed fetching stats: {e}")
        return {
            "total_leads": 0,
            "total_messages": 0,
            "active_conversations": 0,
            "db_status": "offline",
            "provider": "Neon Cloud PostgreSQL"
        }
    finally:
        if conn:
            conn.close()

def create_tenant(tenant_id: str, name: str, phone: str, category: str, knowledge_base: str, website_url: str = "https://shazusofttechnologies.org/software") -> bool:
    """Register a new business client on Shazu Soft Free Beta."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tenants (id, name, phone, category, knowledge_base, custom_prompt, website_url, viral_footer_enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                phone = EXCLUDED.phone,
                category = EXCLUDED.category,
                knowledge_base = EXCLUDED.knowledge_base,
                website_url = EXCLUDED.website_url;
        """, (
            tenant_id,
            name,
            phone,
            category,
            knowledge_base,
            f"Official 24/7 AI Business Consultant for {name}.",
            website_url
        ))

        # Register default instance
        cur.execute("""
            INSERT INTO whatsapp_instances (id, tenant_id, phone, status)
            VALUES (%s, %s, %s, 'initializing')
            ON CONFLICT (id) DO NOTHING;
        """, (f"inst_{tenant_id}", tenant_id, phone))

        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"[DATABASE ERROR] Failed creating tenant: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve tenant details and custom knowledge base."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, name, phone, category, knowledge_base, custom_prompt, website_url, viral_footer_enabled
            FROM tenants
            WHERE id = %s;
        """, (tenant_id,))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[DATABASE ERROR] Failed fetching tenant: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_tenant_knowledge(tenant_id: str, knowledge_base: str) -> bool:
    """Update a business client's knowledge base."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE tenants
            SET knowledge_base = %s
            WHERE id = %s;
        """, (knowledge_base, tenant_id))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_all_tenants() -> List[Dict[str, Any]]:
    """Fetch all registered business clients."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, name, phone, category, website_url, TO_CHAR(created_at, 'YYYY-MM-DD') as created_date
            FROM tenants
            ORDER BY created_at DESC;
        """)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return []
    finally:
        if conn:
            conn.close()
