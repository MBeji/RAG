#!/bin/bash

# Navigate to the directory where the Dockerfile is located, if necessary
# cd "$(dirname "$0")" || exit

# Build the Docker image
echo "Building Docker image rag-chatbot-backend:latest..."
docker build -t rag-chatbot-backend:latest .

if [ $? -eq 0 ]; then
  echo "Docker image built and tagged successfully as rag-chatbot-backend:latest."
else
  echo "Docker image build failed."
  exit 1
fi
