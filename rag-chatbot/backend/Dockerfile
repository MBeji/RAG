# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container at /app
# Ensure these paths are relative to the Dockerfile's location (rag-chatbot/backend/)
COPY app/ ./app/
COPY models/ ./models/
COPY utils/ ./utils/
COPY vector_store/ ./vector_store/
COPY data/ ./data/ 

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable if needed (e.g., for Python path)
ENV PYTHONPATH=/app

# Run main.py when the container launches
# Ensure the command correctly points to the FastAPI app instance
# Assuming the FastAPI app instance in app/main.py is named 'app'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
