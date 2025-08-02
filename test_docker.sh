#!/bin/bash

echo "🐳 Building Global Publisher Docker container..."
docker-compose build

echo ""
echo "🧪 Testing cache operations (no API key needed)..."
docker-compose run --rm global-publisher python3 main.py --cache-stats

echo ""
echo "📅 Testing schedule display (no API key needed)..."
docker-compose run --rm global-publisher python3 main.py sample_content.md --platforms hackernews reddit --schedule

echo ""
echo "🔄 Testing retry functionality (no API key needed)..."
docker-compose run --rm global-publisher python3 main.py --retry

echo ""
echo "🧹 Testing cache cleanup (no API key needed)..."
docker-compose run --rm global-publisher python3 main.py --cleanup-cache

echo ""
echo "🎯 Testing help command..."
docker-compose run --rm global-publisher python3 main.py --help

echo ""
echo "✅ Docker tests completed!"
echo ""
echo "To test with real API keys:"
echo "1. Copy .env.example to .env"
echo "2. Fill in your API keys"
echo "3. Run: docker-compose run --rm global-publisher python3 main.py sample_content.md --platforms hackernews --preview"