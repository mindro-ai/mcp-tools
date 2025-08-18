#!/bin/bash

# ---------------------------
# NocoDB MCP Endpoint Test Script
# ---------------------------

# Set your server URL and endpoint
MCP_URL="http://localhost:8080/nocodb/messages"
SSE_URL="http://localhost:8080/nocodb/sse"

# Generate a random session ID
SESSION_ID=a1cc832a1fa94efb92962dde228c5176

echo "Using session ID: $SESSION_ID"
echo "---------------------------"

# 1️⃣ Initialize MCP session
curl -s -X POST -H "Content-Type: application/json" -d "{
  \"jsonrpc\": \"2.0\",
  \"method\": \"initialize\",
  \"params\": {
    \"protocolVersion\": \"2025-06-18\",
    \"capabilities\": {},
    \"clientInfo\": { \"name\": \"curl-test\", \"version\": \"1.0\" }
  },
  \"id\": 1
}" "$MCP_URL/?session_id=$SESSION_ID"

echo -e "\nSession initialized!"
echo "---------------------------"

# 2️⃣ Call the 'tables' tool to list tables
curl -s -X POST -H "Content-Type: application/json" -d "{
  \"jsonrpc\": \"2.0\",
  \"method\": \"tools/call\",
  \"params\": {
    \"name\": \"tables\",
    \"argument\": { \"base_id\": \"paln7xc91rof9q7\" }
  },
  \"id\": 2
}" "$MCP_URL/?session_id=$SESSION_ID"

echo -e "\nRequest sent to list tables!"
echo "---------------------------"

# 3️⃣ Listen to SSE responses in real-time
echo "Listening for SSE events. Press Ctrl+C to stop."
curl -N -H "Accept: text/event-stream" "$SSE_URL"


curl -s -X POST -H "Content-Type: application/json" -d "{
  \"jsonrpc\": \"2.0\",
  \"method\": \"tools/call\",
  \"params\": {
    \"name\": \"tables\",
    \"argument\": { \"base_id\": \"paln7xc91rof9q7\" }
  },
  \"id\": 2
}" "$MCP_URL/?session_id=$SESSION_ID"