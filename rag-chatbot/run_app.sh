#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting the RAG Chatbot Application..."

# 1. Navigate to Backend Directory
echo "Navigating to backend directory..."
cd backend/

# 2. Run Backend Package Script
echo "Building backend Docker image..."
if [ -f "package.sh" ] && [ -x "package.sh" ]; then
    ./package.sh
else
    echo "Error: backend/package.sh not found or not executable."
    exit 1
fi

# 3. Run Backend Docker Container
CONTAINER_NAME="rag-backend-container"
IMAGE_NAME="rag-chatbot-backend:latest"

echo "Stopping and removing existing backend container if any..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

echo "Running backend Docker container '$CONTAINER_NAME' from image '$IMAGE_NAME'..."
docker run -d -p 8000:8000 --name "$CONTAINER_NAME" "$IMAGE_NAME"

echo "Waiting for backend server to initialize (5 seconds)..."
sleep 5

# Navigate back to the root directory
cd ..

# 4. Navigate to Frontend Directory
echo "Navigating to frontend directory (frontend/chat-ui/)..."
cd frontend/chat-ui/

# 5. Run Frontend Build Script
echo "Building frontend assets..."
if [ -f "build.sh" ] && [ -x "build.sh" ]; then
    # Ensure npm is available before running build
    if ! command -v npm &> /dev/null
    then
        echo "Error: npm could not be found. Please install Node.js and npm."
        exit 1
    fi
    # Run setup if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo "node_modules not found. Running setup.sh..."
        if [ -f "setup.sh" ] && [ -x "setup.sh" ]; then
            ./setup.sh
        else
            echo "Error: frontend/chat-ui/setup.sh not found or not executable, and node_modules is missing."
            exit 1
        fi
    fi
    ./build.sh
else
    echo "Error: frontend/chat-ui/build.sh not found or not executable."
    exit 1
fi

# 6. Serve Frontend Assets
FRONTEND_PORT=8080
BUILD_DIR="dist" # Common build output directory for Vite/React/Vue

if [ ! -d "$BUILD_DIR" ]; then
    echo "Error: Frontend build directory '$BUILD_DIR' not found after build.sh."
    exit 1
fi

echo "Serving frontend assets from '$BUILD_DIR' on port $FRONTEND_PORT..."
# Check if python3 is available
if ! command -v python3 &> /dev/null
then
    echo "Error: python3 could not be found. Cannot start HTTP server for frontend."
    echo "Please install python3 or serve the '$BUILD_DIR' directory using another HTTP server on port $FRONTEND_PORT."
    # Instructions to stop backend
    echo ""
    echo "To stop the backend application:"
    echo "  docker stop $CONTAINER_NAME"
    echo "  docker rm $CONTAINER_NAME"
    exit 1
fi
python3 -m http.server --directory "$BUILD_DIR" "$FRONTEND_PORT" &
FRONTEND_PID=$!
echo "Frontend server started with PID $FRONTEND_PID."

# Navigate back to the root directory
cd ../../

# 7. Provide Instructions
echo ""
echo "----------------------------------------------------"
echo "RAG Chatbot Application Started!"
echo "----------------------------------------------------"
echo "Backend API is running on: http://localhost:8000"
echo "Frontend UI is being served on: http://localhost:$FRONTEND_PORT"
echo ""
echo "To stop the application:"
echo "1. Stop the backend Docker container: docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
echo "2. Stop the frontend server: kill $FRONTEND_PID"
echo ""
echo "Note: If you stop this script with Ctrl+C, the frontend server (PID $FRONTEND_PID) might continue running. Use 'kill $FRONTEND_PID' to stop it."
echo "----------------------------------------------------"

# Keep the script running so user can see the PIDs and instructions.
# The user will typically Ctrl+C to stop this script, which will leave the background processes running.
# An alternative is to use a trap to kill the background processes on exit.
# For simplicity, this script relies on manual cleanup as per instructions.

wait $FRONTEND_PID # Optional: wait for frontend server to exit. If it exits, the script exits.
                  # If user Ctrl+C, this wait is interrupted.
exit 0
