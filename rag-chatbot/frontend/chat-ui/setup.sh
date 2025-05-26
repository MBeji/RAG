#!/bin/bash

# Install Node.js dependencies
echo "Installing Node.js dependencies using npm..."
npm install

if [ $? -eq 0 ]; then
  echo "Dependencies installed successfully."
else
  echo "npm install failed. Please check for errors."
  exit 1
fi
