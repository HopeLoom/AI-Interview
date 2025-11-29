#!/bin/bash
# Start backend in production environment
echo "Starting backend in PRODUCTION mode..."
export STAGE=production
python main.py