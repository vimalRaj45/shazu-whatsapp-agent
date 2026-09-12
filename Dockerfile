# =======================================================
# Shazu Soft Technologies - WhatsApp AI Business Platform
# Production Standalone Dockerfile for Render.com & VPS
# =======================================================

FROM node:20-bookworm-slim

# 1. Install Python 3, pip, and PostgreSQL client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    libpq5 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copy and install Python dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# 3. Copy gateway package specifications and install Node dependencies
COPY gateway/package*.json ./gateway/
RUN cd gateway && npm install --omit=dev

# 4. Copy all application files
COPY . .

# 5. Environment configuration
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# 6. Expose web ports
EXPOSE 10000 3001 5005

# 7. Start unified system runner
CMD ["python3", "run_system.py"]
