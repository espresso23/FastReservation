#!/bin/bash

echo "🚀 Starting All Services for FandBAI Spring"
echo "=========================================="
echo

# Check if required services are running
echo "🔍 Checking prerequisites..."

# Check PostgreSQL
echo "Checking PostgreSQL..."
psql -h localhost -U postgres -d fast_planner_db -c "SELECT 1;" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ PostgreSQL is not running or not accessible"
    echo "Please start PostgreSQL and ensure database 'fast_planner_db' exists"
    exit 1
fi
echo "✅ PostgreSQL is running"

# Check if .env exists in ai-service directory
if [ ! -f "src/main/java/tan/fandbaispring/ai-service/.env" ]; then
    echo "❌ AI Service .env file not found!"
    echo "Please configure AI service first:"
    echo "1. cd src/main/java/tan/fandbaispring/ai-service"
    echo "2. cp env_example.txt .env"
    echo "3. Edit .env with your API keys"
    exit 1
fi
echo "✅ AI Service .env file found"

echo
echo "🚀 Starting services in order:"
echo

# Start AI Service (in background)
echo "1. Starting AI Service..."
cd src/main/java/tan/fandbaispring/ai-service
chmod +x start_ai_service.sh
./start_ai_service.sh &
AI_PID=$!
cd ../../../../..
sleep 5

# Start Spring Boot
echo "2. Starting Spring Boot..."
mvn spring-boot:run &
SPRING_PID=$!
sleep 10

# Start Frontend
echo "3. Starting Frontend..."
cd frontend/partner-portal
npm run dev &
FRONTEND_PID=$!
cd ../..
sleep 5

echo
echo "🎉 All services started!"
echo
echo "📱 Service URLs:"
echo "  - Frontend: http://localhost:5173"
echo "  - Spring Boot: http://localhost:8080"
echo "  - AI Service: http://localhost:8000"
echo "  - AI Docs: http://localhost:8000/docs"
echo
echo "⏹️  Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo
    echo "🛑 Stopping all services..."
    kill $AI_PID 2>/dev/null
    kill $SPRING_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
