#!/bin/bash
set -e

curl -s -c cookies.txt -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password123"}'

echo ""

curl -s -b cookies.txt -X POST http://localhost:8000/api/assistant/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Who are you", "history": []}'
