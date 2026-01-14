FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    mariadb-client \
    redis-tools \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18 (if not available in base image)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set working directory
WORKDIR /workspace

# Copy bench directory
COPY . /workspace/bench

# Install Python dependencies
RUN cd /workspace/bench && \
    python3 -m venv env && \
    ./env/bin/pip install --upgrade pip && \
    ./env/bin/pip install -e ./apps/frappe

# Install bench CLI if not present
RUN cd /workspace/bench && \
    if [ ! -f env/bin/bench ]; then \
        ./env/bin/pip install frappe-bench; \
    fi

# Expose ports
EXPOSE 8080 9000

# Default command
CMD ["bash", "-c", "cd /workspace/bench && source env/bin/activate && bench serve --host 0.0.0.0 --port 8080"]
