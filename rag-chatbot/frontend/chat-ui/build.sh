#!/bin/bash

# Build the frontend application for production
echo "Building the frontend application for production..."
npm run build

if [ $? -eq 0 ]; then
  echo "Frontend application built successfully."
else
  echo "npm run build failed. Please check for errors."
  exit 1
fi
