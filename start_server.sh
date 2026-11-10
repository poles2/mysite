#!/bin/bash
echo "=========================================="
echo "  Speed Lightning Payout Server Setup"
echo "=========================================="
cd "$(dirname "$0")"
echo "Installing dependencies (npm install)..."
npm install
echo ""
echo "Starting server..."
node server.js
