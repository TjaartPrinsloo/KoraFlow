#!/bin/bash
#
# KoraFlow Services Restart Script
# Stops and starts all services: Docker (DB, Redis, RAG, LLM), Frappe, and Ollama
#
# Usage:
#   ./restart_all_services.sh         # Stop and start all services
#   ./restart_all_services.sh stop    # Stop all services only
#   ./restart_all_services.sh start   # Start all services only
#   ./restart_all_services.sh status  # Check status of all services
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KORAFLOW_DIR="/Users/tjaartprinsloo/Documents/KoraFlow"
BENCH_DIR="${KORAFLOW_DIR}/bench"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================================
# STOP FUNCTIONS
# ============================================================================

stop_frappe() {
    log_info "Stopping Frappe/Bench processes..."
    pkill -f "frappe serve" 2>/dev/null || true
    pkill -f "frappe.utils.bench_helper" 2>/dev/null || true
    pkill -f "bench start" 2>/dev/null || true
    sleep 2
    log_success "Frappe processes stopped"
}

stop_docker_services() {
    log_info "Stopping Docker services..."
    cd "${KORAFLOW_DIR}"
    if docker-compose ps -q 2>/dev/null | xargs docker inspect -f '{{.State.Running}}' 2>/dev/null | grep -q true; then
        docker-compose down --remove-orphans 2>/dev/null || true
    fi
    log_success "Docker services stopped"
}

stop_ollama() {
    log_info "Stopping Ollama..."
    pkill -f "ollama" 2>/dev/null || true
    log_success "Ollama stopped"
}

stop_local_mariadb() {
    log_info "Stopping local MariaDB (if running)..."
    mysql.server stop 2>/dev/null || true
    log_success "Local MariaDB stopped"
}

stop_all() {
    echo ""
    echo "=========================================="
    echo "  STOPPING ALL KORAFLOW SERVICES"
    echo "=========================================="
    echo ""
    
    stop_frappe
    stop_docker_services
    stop_ollama
    stop_local_mariadb
    
    echo ""
    log_success "All services stopped!"
    echo ""
}

# ============================================================================
# START FUNCTIONS
# ============================================================================

start_docker_services() {
    log_info "Starting Docker services (MariaDB, Redis, RAG, LLM)..."
    cd "${KORAFLOW_DIR}"
    
    # Start docker-compose services
    docker-compose up -d 2>/dev/null
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check MariaDB
    for i in {1..30}; do
        if docker-compose exec -T mariadb mysqladmin ping -h localhost 2>/dev/null | grep -q "alive"; then
            log_success "MariaDB is ready (port 3307)"
            break
        fi
        sleep 2
    done
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis is ready (port 6380)"
    else
        log_warn "Redis may not be responding"
    fi
    
    log_success "Docker services started"
}

start_ollama() {
    log_info "Starting Ollama..."
    
    # Check if Ollama is installed
    if command -v ollama &>/dev/null; then
        # Start Ollama in background
        nohup ollama serve > /tmp/ollama.log 2>&1 &
        sleep 3
        
        # Check if it's running
        if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "models"; then
            log_success "Ollama is running (port 11434)"
        else
            log_warn "Ollama may still be starting..."
        fi
    else
        log_warn "Ollama not installed - skipping"
    fi
}

start_frappe() {
    log_info "Starting Frappe/Bench..."
    cd "${BENCH_DIR}"
    
    # Activate virtual environment and start bench
    source env/bin/activate 2>/dev/null || true
    
    # Start bench serve in background
    nohup bench serve --port 8080 > /tmp/bench_serve.log 2>&1 &
    
    sleep 5
    
    # Check if it's running
    if curl -s -m 5 http://localhost:8080 2>/dev/null | grep -q ""; then
        log_success "Frappe is running (port 8080)"
    else
        log_warn "Frappe may still be starting - check /tmp/bench_serve.log"
    fi
}

start_all() {
    echo ""
    echo "=========================================="
    echo "  STARTING ALL KORAFLOW SERVICES"
    echo "=========================================="
    echo ""
    
    start_docker_services
    start_ollama
    start_frappe
    
    echo ""
    log_success "All services started!"
    echo ""
}

# ============================================================================
# STATUS FUNCTION
# ============================================================================

check_status() {
    echo ""
    echo "=========================================="
    echo "  KORAFLOW SERVICES STATUS"
    echo "=========================================="
    echo ""
    
    # Docker services
    log_info "Docker services:"
    cd "${KORAFLOW_DIR}"
    docker-compose ps 2>/dev/null || log_warn "Docker-compose not available"
    
    echo ""
    
    # MariaDB
    if docker-compose exec -T mariadb mysqladmin ping -h localhost 2>/dev/null | grep -q "alive"; then
        log_success "MariaDB: RUNNING (port 3307)"
    else
        log_error "MariaDB: NOT RUNNING"
    fi
    
    # Redis
    if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis: RUNNING (port 6380)"
    else
        log_error "Redis: NOT RUNNING"
    fi
    
    # Ollama
    if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "models"; then
        log_success "Ollama: RUNNING (port 11434)"
    else
        log_error "Ollama: NOT RUNNING"
    fi
    
    # Frappe
    if curl -s -m 5 http://localhost:8080/api/method/frappe.ping 2>/dev/null | grep -q "pong"; then
        log_success "Frappe: RUNNING (port 8080)"
    elif lsof -i :8080 2>/dev/null | grep -q LISTEN; then
        log_warn "Frappe: LISTENING but not responding (may be starting)"
    else
        log_error "Frappe: NOT RUNNING"
    fi
    
    # LLM Service
    if curl -s -m 5 http://localhost:8000/health 2>/dev/null | grep -q ""; then
        log_success "LLM Service: RUNNING (port 8000)"
    else
        log_warn "LLM Service: NOT RUNNING or not responding"
    fi
    
    echo ""
}

# ============================================================================
# CONNECTION TEST
# ============================================================================

test_connections() {
    echo ""
    echo "=========================================="
    echo "  TESTING ALL CONNECTIONS"
    echo "=========================================="
    echo ""
    
    # Test MariaDB connection
    log_info "Testing MariaDB connection..."
    if docker-compose exec -T mariadb mysql -u root -padmin -e "SELECT 1" 2>/dev/null; then
        log_success "MariaDB connection: OK"
    else
        log_error "MariaDB connection: FAILED"
    fi
    
    # Test Redis connection  
    log_info "Testing Redis connection..."
    if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis connection: OK"
    else
        log_error "Redis connection: FAILED"
    fi
    
    # Test Frappe API
    log_info "Testing Frappe API..."
    if curl -s -m 10 http://localhost:8080/api/method/frappe.ping 2>/dev/null | grep -q "pong"; then
        log_success "Frappe API: OK"
    else
        log_error "Frappe API: FAILED (may still be starting)"
    fi
    
    # Test Sales Agent Dashboard API
    log_info "Testing Sales Agent Dashboard API..."
    if curl -s -m 10 "http://localhost:8080/api/method/koraflow_core.api.sales_agent_dashboard.get_dashboard_data" 2>/dev/null | grep -q "commission_summary\|error"; then
        log_success "Sales Agent Dashboard API: OK"
    else
        log_warn "Sales Agent Dashboard API: No response"
    fi
    
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

case "${1:-restart}" in
    stop)
        stop_all
        ;;
    start)
        start_all
        check_status
        ;;
    status)
        check_status
        ;;
    test)
        test_connections
        ;;
    restart|*)
        stop_all
        sleep 3
        start_all
        sleep 5
        check_status
        test_connections
        ;;
esac

echo ""
echo "=========================================="
echo "  DONE"
echo "=========================================="
echo ""
echo "Access points:"
echo "  - Frappe:     http://localhost:8080"
echo "  - LLM API:    http://localhost:8000"
echo "  - Ollama:     http://localhost:11434"
echo ""
