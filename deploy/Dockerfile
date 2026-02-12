FROM frappe/bench:latest

USER root
# Install git and other runtime dependencies
RUN apt-get update && apt-get install -y git && apt-get clean

# Ensure the bench directory exists and is owned by frappe
RUN mkdir -p /home/frappe/bench && chown -R frappe:frappe /home/frappe/bench

USER frappe
WORKDIR /home/frappe/bench

# Initialize a new bench (skip redis/mariadb setup as we use external)
RUN bench init --skip-redis-config-generation --skip-assets --python python3 frappe-bench

WORKDIR /home/frappe/bench/frappe-bench

# Get the custom app from the repo-relative path
# Build context must be the repo root (KoraFlow/)
COPY --chown=frappe:frappe bench/apps/koraflow_core /home/frappe/bench/frappe-bench/apps/koraflow_core

# Install the custom app and register it with Frappe
RUN ./env/bin/pip install -e apps/koraflow_core \
    && printf '\nkoraflow_core\n' >> sites/apps.txt

# Create logs directory (prevents cssutils.log FileNotFoundError)
RUN mkdir -p /home/frappe/bench/logs

# Copy the safe migrate script
COPY --chown=frappe:frappe deploy/safe_migrate.sh /home/frappe/bench/frappe-bench/safe_migrate.sh
USER root
RUN chmod +x /home/frappe/bench/frappe-bench/safe_migrate.sh
USER frappe

# Build assets
RUN bench build

# Configure defaults for Docker Compose networking
# These are baked into the image so ephemeral containers (bench new-site) work
RUN bench set-config -g db_type mariadb \
    && bench set-config -g db_host mariadb \
    && bench set-config -g db_port 3306 \
    && bench set-config -g redis_cache "redis://:koraflow_redis_2026@redis:6379/0" \
    && bench set-config -g redis_queue "redis://:koraflow_redis_2026@redis:6379/1" \
    && bench set-config -g redis_socketio "redis://:koraflow_redis_2026@redis:6379/2"

EXPOSE 8000

# Use the production entrypoint
CMD ["/home/frappe/bench/frappe-bench/env/bin/gunicorn", "-b", "0.0.0.0:8000", "-w", "4", "-t", "120", "--worker-class", "gthread", "--threads", "4", "frappe.app:application"]
