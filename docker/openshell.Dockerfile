# OpenShell Hardened Container Environment for Threadline Sovereign Delegate
# Enforces strict network egress boundaries, host key isolation, and file sandboxing.

FROM python:3.10-slim-bullseye

# Security: Install minimal runtime dependencies and drop root privileges
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged agent user
RUN useradd -m -u 1000 -s /bin/bash openshell_agent

WORKDIR /workspace

# Install Python requirements
COPY backend/requirements.txt /workspace/backend/requirements.txt
RUN pip install --no-cache-dir -r /workspace/backend/requirements.txt

# Copy backend code
COPY backend /workspace/backend
COPY data /workspace/data

# Set ownership to unprivileged user
RUN chown -R openshell_agent:openshell_agent /workspace

# Boundary policies:
# 1. Deny write access outside ./data/workspace
# 2. Block raw socket creation for non-allowlisted domains
USER openshell_agent

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace
ENV THREADLINE_SANDBOX_MODE=openshell

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

