#!/bin/bash

# Zizo_NetVerse Backend Setup Script
# Run this script on your DigitalOcean droplet to set up the backend

echo "🚀 Setting up Zizo_NetVerse Backend Engine..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and required system packages
echo "🐍 Installing Python and system dependencies..."
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential
sudo apt install -y redis-server
sudo apt install -y libpcap-dev  # Required for scapy packet capture

# Install InfluxDB
echo "📊 Installing InfluxDB..."
curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
echo "deb https://repos.influxdata.com/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt update
sudo apt install -y influxdb2

# Start services
echo "🔧 Starting services..."
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl start influxdb
sudo systemctl enable influxdb

# Create Python virtual environment
echo "🛠️ Setting up Python environment..."
cd src/backend
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up InfluxDB
echo "🗄️ Setting up InfluxDB..."
echo "Please run the following commands manually after this script completes:"
echo "1. sudo influx setup --username admin --password yourpassword --org zizo-netverse --bucket network-logs"
echo "2. influx auth create --org zizo-netverse --all-access"
echo "3. Copy the generated token to your .env file"

# Set permissions for packet capture
echo "🔒 Setting up packet capture permissions..."
echo "To allow packet capture without root, run:"
echo "sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3"

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your .env file with proper InfluxDB token"
echo "2. Add your Firebase service account key to core/serviceAccountKey.json"
echo "3. Run: uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "🔥 Your cybersecurity command deck backend is ready!"
