#!/bin/bash

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
  echo "Virtual environment not found. Running setup.sh first."
  # Make sure setup.sh is executable and run it
  if [ ! -f "setup.sh" ]; then
    echo "setup.sh not found. Please create it first."
    exit 1
  fi
  chmod +x setup.sh
  ./setup.sh
  # Exit if setup failed (e.g. python3 or venv not installed)
  if [ $? -ne 0 ]; then
    echo "Setup failed. Please check python3 and venv are installed and try again."
    exit 1
  fi
fi

# Activate the virtual environment
source .venv/bin/activate

# Run the FastAPI application
echo "Starting FastAPI application with Uvicorn..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
