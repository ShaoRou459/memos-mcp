#!/bin/bash

# MCP Memos Server Setup Script
set -e

echo "🚀 Setting up MCP Memos Server..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️ Please edit .env with your Memos server details before continuing"
    echo ""
    echo "Required configuration:"
    echo "  - MEMOS_URL: Your Memos server URL"
    echo "  - MEMOS_API_KEY: Your Memos API key"
    echo ""
    read -p "Press Enter after you've configured .env..."
else
    echo "✅ Found existing .env file"
fi

# Check if Docker is available
if command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
    echo "🐳 Docker detected"
    
    read -p "Do you want to build and run with Docker? [Y/n]: " use_docker
    use_docker=${use_docker:-y}
    
    if [[ $use_docker =~ ^[Yy]$ ]]; then
        echo "🔨 Building Docker image..."
        docker-compose build
        
        echo "✅ Docker image built successfully"
        echo ""
        echo "To run the server:"
        echo "  docker-compose up -d"
        echo ""
        echo "To view logs:"
        echo "  docker-compose logs -f mcp-memos-server"
        echo ""
        echo "To stop the server:"
        echo "  docker-compose down"
        echo ""
        
        read -p "Start the server now? [Y/n]: " start_now
        start_now=${start_now:-y}
        
        if [[ $start_now =~ ^[Yy]$ ]]; then
            echo "🚀 Starting MCP Memos Server..."
            docker-compose up -d
            sleep 2
            echo "📋 Checking server status..."
            docker-compose logs --tail=20 mcp-memos-server
        fi
        
        exit 0
    fi
fi

# Python setup
echo "🐍 Setting up Python environment..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required, but found Python $python_version"
    echo "Please upgrade Python or use Docker instead"
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Run tests
echo ""
echo "🧪 Running tests to verify setup..."
read -p "Run tests now? [Y/n]: " run_tests
run_tests=${run_tests:-y}

if [[ $run_tests =~ ^[Yy]$ ]]; then
    python test_server.py
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the server:"
echo "  source venv/bin/activate"
echo "  python server.py"
echo ""
echo "To configure with Claude Desktop, add this to your MCP config:"
echo '{'
echo '  "mcpServers": {'
echo '    "memos": {'
echo '      "command": "python",'
echo "      \"args\": [\"$(pwd)/server.py\"],"
echo '      "env": {'
echo "        \"MEMOS_URL\": \"$(grep MEMOS_URL .env | cut -d '=' -f2)\","
echo "        \"MEMOS_API_KEY\": \"$(grep MEMOS_API_KEY .env | cut -d '=' -f2)\""
echo '      }'
echo '    }'
echo '  }'
echo '}'