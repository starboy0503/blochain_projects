#!/bin/bash
# start_nodes.sh
# Run Node A (5001) and Node B (5002) + auto-register peers

BASE_DIR=~/Desktop/blockchain
NODE_A_DIR=$BASE_DIR/project2/p2p_blockchain_chat
NODE_B_DIR=$BASE_DIR/project2nodeb/p2p_blockchain_chat

# Kill any old servers on 5001/5002
echo "🔴 Stopping any old Flask servers on 5001/5002..."
lsof -ti:5001 -ti:5002 | xargs kill -9 2>/dev/null

# Start Node A
echo "🚀 Starting Node A on port 5001..."
cd $NODE_A_DIR
PORT=5001 python3 node.py > nodeA.log 2>&1 &
PID_A=$!

# Start Node B
echo "🚀 Starting Node B on port 5002..."
cd $NODE_B_DIR
PORT=5002 python3 node.py > nodeB.log 2>&1 &
PID_B=$!

# Wait for servers to boot
sleep 3

# Register peers
echo "🔗 Registering Node A ↔ Node B..."
curl -s -X POST http://127.0.0.1:5001/peers/register \
     -H "Content-Type: application/json" \
     -d '{"host": "http://127.0.0.1:5002"}' > /dev/null

curl -s -X POST http://127.0.0.1:5002/peers/register \
     -H "Content-Type: application/json" \
     -d '{"host": "http://127.0.0.1:5001"}' > /dev/null

echo "✅ Nodes are running!"
echo "   Node A → http://127.0.0.1:5001"
echo "   Node B → http://127.0.0.1:5002"
echo "   Logs: nodeA.log, nodeB.log"
echo "   To stop: kill $PID_A $PID_B"
