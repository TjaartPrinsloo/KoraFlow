#!/bin/bash
# KoraFlow Complete Installation Script
# This script installs everything needed to get KoraFlow running from scratch

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "KoraFlow Complete Installation"
echo "=========================================="
echo ""
echo "This script will install all dependencies and set up KoraFlow."
echo "It may take 30-60 minutes depending on your internet connection."
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Check and install system prerequisites
echo ""
echo "=========================================="
echo "Step 1: Checking System Prerequisites"
echo "=========================================="
echo ""

# Check Git
if command_exists git; then
    print_status "Git is installed"
else
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

# Check Docker
if command_exists docker; then
    if docker info > /dev/null 2>&1; then
        print_status "Docker is installed and running"
    else
        print_error "Docker is installed but not running. Please start Docker first."
        exit 1
    fi
else
    print_error "Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

# Check Docker Compose
if docker compose version > /dev/null 2>&1 || docker-compose version > /dev/null 2>&1; then
    print_status "Docker Compose is available"
else
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Check Homebrew (for macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if command_exists brew; then
        print_status "Homebrew is installed"
    else
        print_warning "Homebrew is not installed. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH
        if [ -f /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -f /usr/local/bin/brew ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        print_status "Homebrew installed"
    fi
fi

# Step 2: Check and install Python 3.10+
echo ""
echo "=========================================="
echo "Step 2: Checking Python Installation"
echo "=========================================="
echo ""

if command_exists python3; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        print_status "Python $PYTHON_VERSION is installed (3.10+ required)"
    else
        print_warning "Python $PYTHON_VERSION is installed, but 3.10+ is required"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_warning "Installing Python 3.10 via Homebrew..."
            brew install python@3.10
            # Update PATH
            export PATH="/opt/homebrew/opt/python@3.10/bin:$PATH" || export PATH="/usr/local/opt/python@3.10/bin:$PATH"
            print_status "Python 3.10 installed"
        else
            print_error "Please install Python 3.10+ manually"
            exit 1
        fi
    fi
else
    print_error "Python 3 is not installed"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_warning "Installing Python 3.10 via Homebrew..."
        brew install python@3.10
        export PATH="/opt/homebrew/opt/python@3.10/bin:$PATH" || export PATH="/usr/local/opt/python@3.10/bin:$PATH"
        print_status "Python 3.10 installed"
    else
        print_error "Please install Python 3.10+ manually"
        exit 1
    fi
fi

# Step 3: Install system dependencies
echo ""
echo "=========================================="
echo "Step 3: Installing System Dependencies"
echo "=========================================="
echo ""

if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ -f "$SCRIPT_DIR/install_system_dependencies.sh" ]; then
        chmod +x "$SCRIPT_DIR/install_system_dependencies.sh"
        "$SCRIPT_DIR/install_system_dependencies.sh" || print_warning "Some system dependencies may have failed to install"
    else
        print_warning "install_system_dependencies.sh not found, skipping system dependencies"
    fi
else
    print_warning "System dependencies installation script is for macOS. Please install manually:"
    print_warning "  - libmagic (for Drive)"
    print_warning "  - pkg-config and mariadb development libraries (for Insights)"
fi

# Step 4: Check and install Node.js
echo ""
echo "=========================================="
echo "Step 4: Checking Node.js Installation"
echo "=========================================="
echo ""

if command_exists node; then
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -ge 18 ]; then
        print_status "Node.js $(node --version) is installed (18+ required)"
    else
        print_warning "Node.js version is too old. Installing Node.js 18+..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install node@18
            export PATH="/opt/homebrew/opt/node@18/bin:$PATH" || export PATH="/usr/local/opt/node@18/bin:$PATH"
        else
            print_error "Please install Node.js 18+ manually"
            exit 1
        fi
    fi
else
    print_warning "Node.js is not installed. Installing Node.js 18+..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install node@18
        export PATH="/opt/homebrew/opt/node@18/bin:$PATH" || export PATH="/usr/local/opt/node@18/bin:$PATH"
    else
        print_error "Please install Node.js 18+ manually"
        exit 1
    fi
    print_status "Node.js installed"
fi

# Step 5: Install and setup Ollama
echo ""
echo "=========================================="
echo "Step 5: Setting up Ollama"
echo "=========================================="
echo ""

if command_exists ollama; then
    print_status "Ollama is installed"
    
    # Check if Ollama is running
    if ollama list > /dev/null 2>&1; then
        print_status "Ollama is running"
    else
        print_warning "Starting Ollama server..."
        # Start Ollama in background (macOS)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open -a Ollama || ollama serve &
            sleep 5
        else
            ollama serve &
            sleep 5
        fi
    fi
else
    print_warning "Ollama is not installed. Installing Ollama..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ollama
    else
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
    
    # Start Ollama
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open -a Ollama || ollama serve &
        sleep 5
    else
        ollama serve &
        sleep 5
    fi
    print_status "Ollama installed and started"
fi

# Pull required models
echo ""
echo "Pulling required Ollama models (this may take a while)..."
echo "  - llama3 (LLM model)"
ollama pull llama3 || print_warning "Failed to pull llama3, you can pull it manually later"
echo "  - nomic-embed-text (embedding model)"
ollama pull nomic-embed-text || print_warning "Failed to pull nomic-embed-text, you can pull it manually later"
print_status "Ollama models ready"

# Step 6: Setup Bench and Frappe
echo ""
echo "=========================================="
echo "Step 6: Setting up Bench and Frappe"
echo "=========================================="
echo ""

# Install Bench CLI
if command_exists bench; then
    print_status "Bench CLI is installed"
else
    print_warning "Installing Bench CLI..."
    pip3 install --user frappe-bench
    
    # Add user bin to PATH
    if [[ -d "$HOME/Library/Python/3.9/bin" ]]; then
        export PATH="$HOME/Library/Python/3.9/bin:$PATH"
    elif [[ -d "$HOME/Library/Python/3.10/bin" ]]; then
        export PATH="$HOME/Library/Python/3.10/bin:$PATH"
    elif [[ -d "$HOME/Library/Python/3.11/bin" ]]; then
        export PATH="$HOME/Library/Python/3.11/bin:$PATH"
    elif [[ -d "$HOME/.local/bin" ]]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # If still not found, try with sudo
    if ! command_exists bench; then
        print_warning "Attempting system-wide install (may require password)..."
        sudo pip3 install frappe-bench
    fi
    print_status "Bench CLI installed"
fi

# Run bench setup
if [ -f "$SCRIPT_DIR/bench_setup.sh" ]; then
    chmod +x "$SCRIPT_DIR/bench_setup.sh"
    print_warning "Running Bench setup (this will take 10-20 minutes)..."
    "$SCRIPT_DIR/bench_setup.sh" || {
        print_error "Bench setup failed. Please check the error messages above."
        exit 1
    }
    print_status "Bench and Frappe setup complete"
else
    print_error "bench_setup.sh not found"
    exit 1
fi

# Step 7: Install KoraFlow Core app
echo ""
echo "=========================================="
echo "Step 7: Installing KoraFlow Core App"
echo "=========================================="
echo ""

BENCH_DIR="$SCRIPT_DIR/bench"
if [ -d "$BENCH_DIR" ]; then
    cd "$BENCH_DIR"
    
    # Get KoraFlow Core app
    if [ ! -d "apps/koraflow_core" ]; then
        print_warning "Installing KoraFlow Core app..."
        bench get-app koraflow_core "$SCRIPT_DIR/apps/koraflow_core"
        bench --site koraflow-site install-app koraflow_core
        print_status "KoraFlow Core app installed"
    else
        print_status "KoraFlow Core app already installed"
    fi
    
    # Build assets
    print_warning "Building assets..."
    bench build
    print_status "Assets built"
    
    cd "$SCRIPT_DIR"
else
    print_error "Bench directory not found"
    exit 1
fi

# Step 8: Build Docker images
echo ""
echo "=========================================="
echo "Step 8: Building Docker Images"
echo "=========================================="
echo ""

print_warning "Building Docker images (this may take a few minutes)..."
docker-compose build
print_status "Docker images built"

# Step 9: Run ingestion pipeline
echo ""
echo "=========================================="
echo "Step 9: Running Ingestion Pipeline"
echo "=========================================="
echo ""

print_warning "Running ingestion pipeline (this will take 15-30 minutes)..."
if [ -f "$SCRIPT_DIR/scripts/run_pipeline.sh" ]; then
    chmod +x "$SCRIPT_DIR/scripts/run_pipeline.sh"
    "$SCRIPT_DIR/scripts/run_pipeline.sh" || {
        print_warning "Ingestion pipeline had some errors, but continuing..."
    }
else
    print_warning "Running ingestion steps manually..."
    docker-compose run --rm ingestion python clone_repos.py || print_warning "Clone repos step had errors"
    docker-compose run --rm ingestion python scrape_docs.py || print_warning "Scrape docs step had errors"
    docker-compose run --rm ingestion python parse_code.py || print_warning "Parse code step had errors"
    docker-compose run --rm ingestion python chunk_documents.py || print_warning "Chunk documents step had errors"
fi
print_status "Ingestion pipeline complete"

# Step 10: Build FAISS index
echo ""
echo "=========================================="
echo "Step 10: Building FAISS Vector Index"
echo "=========================================="
echo ""

print_warning "Building FAISS index (this will take 10-20 minutes)..."
docker-compose run --rm vector_store python faiss_manager.py || {
    print_error "FAISS index build failed"
    exit 1
}
print_status "FAISS index built"

# Step 11: Start all services
echo ""
echo "=========================================="
echo "Step 11: Starting All Services"
echo "=========================================="
echo ""

print_warning "Starting Docker services..."
docker-compose up -d
print_status "Docker services started"

# Wait a moment for services to start
sleep 5

# Check service status
echo ""
echo "Service Status:"
docker-compose ps

# Step 12: Final instructions
echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "KoraFlow is now installed and running!"
echo ""
echo "Next Steps:"
echo ""
echo "1. Start Frappe/Bench development server:"
echo "   cd bench"
echo "   bench start"
echo ""
echo "2. Access KoraFlow:"
echo "   URL: http://localhost:8000"
echo "   Site: koraflow-site"
echo "   Admin credentials: Administrator / admin"
echo ""
echo "3. Test RAG Pipeline:"
echo "   curl http://localhost:8000/health"
echo "   curl -X POST http://localhost:8000/query \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"query\": \"How do I create a custom DocType?\"}'"
echo ""
echo "4. View service logs:"
echo "   docker-compose logs -f llm_service"
echo ""
echo "5. Stop services:"
echo "   docker-compose down"
echo "   cd bench && bench stop"
echo ""
echo "=========================================="
echo ""

