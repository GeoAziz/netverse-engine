#!/bin/bash
# install_dependencies.sh - Install system dependencies for Zizo_NetVerse Backend

echo "🔥 Installing Zizo_NetVerse Backend Dependencies..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update

# Install Python and pip if not already installed
echo "🐍 Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install Redis Server
echo "🚀 Installing Redis Server..."
sudo apt install -y redis-server

# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

echo "✅ Redis Server installed and started"

# Install InfluxDB
echo "💾 Installing InfluxDB..."
curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
echo "deb https://repos.influxdata.com/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt update
sudo apt install -y influxdb

# Start and enable InfluxDB
sudo systemctl start influxdb
sudo systemctl enable influxdb

echo "✅ InfluxDB installed and started"

# Install network tools for packet capture
echo "🌐 Installing network tools..."
sudo apt install -y tcpdump net-tools

echo "🎯 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "🚀 Installation Complete!"
echo ""
echo "Next steps:"
echo "1. Configure InfluxDB:"
echo "   - Visit http://localhost:8086"
echo "   - Set up initial user and organization"
echo "   - Create a bucket called 'network-logs'"
echo "   - Generate an API token"
echo "   - Update the .env file with your token"
echo ""
echo "2. To run the backend:"
echo "   source venv/bin/activate"
echo "   sudo python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "⚠️  Note: Packet capture requires root privileges!"
