#!/bin/bash

# TCP Sliding Window Protocol - Start Script
# Author: Xiangyi Li (xiangyi@benchflow.ai)

echo "TCP Sliding Window Protocol - Starting Application"
echo "=================================================="

# Kill any existing processes on port 12345
echo "Checking for existing processes on port 12345..."
pid=$(lsof -t -i:12345 2>/dev/null)
if [ ! -z "$pid" ]; then
    echo "Killing process $pid on port 12345"
    kill -9 $pid
fi

# Create output directory if it doesn't exist
mkdir -p output

# Copy the fixed server to the main server file
echo "Installing fixed server implementation..."
cp -f server_fixed.py server.py
chmod +x server.py

# Start the server in the background
echo "Starting TCP server on port 12345..."
python3 server.py &
SERVER_PID=$!

# Wait for server to initialize
echo "Waiting for server to initialize..."
sleep 2

# Start the client
echo "Starting TCP client..."
python3 client.py

# Wait for client to finish
wait $SERVER_PID

echo "=================================================="
echo "TCP Sliding Window Protocol - Execution Complete"
echo "Check the output directory for results and visualizations"
