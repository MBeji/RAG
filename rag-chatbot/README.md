# RAG Chatbot

## Overview

This project is a web application that allows users to upload documents and chat with a Large Language Model (LLM) about their content. It utilizes a Retrieval Augmented Generation (RAG) architecture to provide contextually relevant answers based on the uploaded documents.

**Key Features:**
*   **File Upload:** Supports PDF, TXT, DOCX, Markdown (.md), and CSV files.
*   **Drag-and-Drop:** Convenient file uploading by dragging files onto the UI.
*   **Text Processing:** Extracts text from various document formats.
*   **Vector Storage:** Uses ChromaDB to store embeddings of document chunks.
*   **LLM Integration:** Leverages local LLMs via Ollama (e.g., Llama 2, Mistral).
*   **Chat Interface:** User-friendly interface for interacting with the LLM.
*   **Streaming Responses:** LLM responses are streamed token by token for a real-time feel.
*   **Conversation History:** Chat history is saved in the browser's `localStorage`.
*   **Relevance Filtering:** (Backend capability) Option to filter retrieved documents by a relevance score.
*   **Selectable Embedding Models:** (Backend capability) Supports different sentence-transformer models for embeddings.

## Architecture

*   **Frontend:** React (built with Vite) and styled with Tailwind CSS.
*   **Backend:** FastAPI (Python).
*   **Vector Database:** ChromaDB (persistent storage).
*   **LLM:** Ollama for local LLM hosting and inference.
*   **Core Logic:** Langchain for RAG pipeline components (text splitting, interacting with ChromaDB, and LLM integration).

## Project Structure

```
rag-chatbot/
├── backend/        # FastAPI application, RAG logic, LLM integration
│   ├── app/        # Core application logic, API endpoints
│   ├── models/     # LLM interaction module
│   ├── utils/      # Text parsing, chunking utilities
│   └── vector_store/ # ChromaDB interaction module
├── frontend/
│   └── chat-ui/    # React + Vite frontend application
├── data/           # Stores uploaded user documents (created automatically by backend)
├── vector_db/      # Stores ChromaDB vector data (created automatically by backend)
└── README.md       # This file
```

## Setup and Running the Application

This section describes how to set up and run the RAG Chatbot application using the provided helper scripts.

### Prerequisites

*   **Node.js and npm:** For the frontend. (Download from [nodejs.org](https://nodejs.org/))
*   **Python 3.8+ and pip:** For the backend. (Download from [python.org](https://www.python.org/))
*   **Docker:** Required for using `package.sh` (backend) and the main `run_app.sh` script. (Download from [docker.com](https://www.docker.com/products/docker-desktop/))
*   **Ollama:** Installed and running. (Download and instructions: [https://ollama.com](https://ollama.com))
    *   Ensure Ollama is running and accessible.
    *   You need to have at least one model pulled. Examples:
        ```bash
        ollama pull llama2
        ollama pull mistral
        ```
    *   Verify available models with `ollama list`.

### Available Scripts

The project includes several scripts to help with setup, development, and packaging:

**1. Backend Scripts (`rag-chatbot/backend/`)**

*   `setup.sh`:
    *   Creates a Python virtual environment (`.venv`).
    *   Activates the environment.
    *   Installs required Python dependencies from `requirements.txt`.
*   `run_dev.sh`:
    *   Activates the Python virtual environment (if not already active, and runs `setup.sh` if `.venv` is missing).
    *   Runs the backend FastAPI application in development mode using `uvicorn` (with auto-reload).
    *   The backend will typically be available at `http://localhost:8000`.
*   `package.sh`:
    *   Builds a Docker image for the backend application using the `Dockerfile`, tagged as `rag-chatbot-backend:latest`.
*   `Dockerfile`:
    *   Contains instructions to build the backend Docker image.

**2. Frontend Scripts (`rag-chatbot/frontend/chat-ui/`)**

*   `setup.sh`:
    *   Installs Node.js dependencies using `npm install`.
*   `run_dev.sh`:
    *   Runs the frontend React application in development mode using Vite (`npm run dev`).
    *   The frontend will typically be available at `http://localhost:5173` (Vite will indicate the URL).
*   `build.sh`:
    *   Builds the frontend application for production (outputs to `frontend/chat-ui/dist/`).

**3. Root Scripts (`rag-chatbot/`)**

*   `run_app.sh`:
    *   This is the **recommended script for most users** to get the application running locally.
    *   It automates the following:
        1.  Navigates to the `backend/` directory.
        2.  Runs `backend/package.sh` to build the backend Docker image.
        3.  Stops and removes any existing backend Docker container named `rag-backend-container`.
        4.  Runs the backend Docker container (`rag-chatbot-backend:latest`) in detached mode. The backend API will be available on `http://localhost:8000`.
        5.  Navigates to the `frontend/chat-ui/` directory.
        6.  Runs `frontend/chat-ui/setup.sh` if `node_modules` are not found.
        7.  Runs `frontend/chat-ui/build.sh` to build the frontend static assets.
        8.  Serves the built frontend assets (from `frontend/chat-ui/dist/`) using a simple Python HTTP server on `http://localhost:8080`.
    *   **Stopping the application:** The `run_app.sh` script will print instructions on how to stop the services. This typically involves:
        *   Stopping the backend Docker container: `docker stop rag-backend-container && docker rm rag-backend-container`
        *   Stopping the frontend Python HTTP server: `kill <PID>` (the PID will be displayed by the script when it starts the server). You can also stop the `run_app.sh` script itself with Ctrl+C.
*   `deploy.sh`:
    *   A placeholder script providing guidance and a template for deploying the application to a cloud environment.
    *   **This script requires significant customization** based on your specific deployment target and infrastructure. It is not intended to be run as-is.

### Running the Application Locally

**Recommended Method (using `run_app.sh`):**

1.  **Clone the repository:**
    ```bash
    git clone <repository-url> # Replace <repository-url> with the actual URL
    cd rag-chatbot
    ```
2.  **Ensure Prerequisites are met:**
    *   Docker is installed and running.
    *   Ollama is installed, running, and has models (e.g., `ollama pull llama2`).
    *   Node.js and Python are installed (for the build steps within `run_app.sh`).
3.  **Make scripts executable (if necessary, one time only):**
    While the scripts should have executable permissions set by git if committed correctly, you can ensure this:
    ```bash
    chmod +x run_app.sh backend/setup.sh backend/run_dev.sh backend/package.sh frontend/chat-ui/setup.sh frontend/chat-ui/run_dev.sh frontend/chat-ui/build.sh
    ```
4.  **Run the application:**
    ```bash
    ./run_app.sh
    ```
5.  **Access the application:**
    *   Backend API: `http://localhost:8000`
    *   Frontend UI: `http://localhost:8080`
6.  **Follow the instructions printed by `run_app.sh` to stop the application.**

**Alternative: Manual Development Setup**

This method allows you to run the frontend and backend development servers separately, which can be useful for active development and debugging.

1.  **Clone the repository and navigate into its root directory.**
2.  **Ensure Prerequisites are met** (Ollama, Node.js, Python).
3.  **Set up and run the Backend:**
    ```bash
    cd backend
    ./setup.sh  # Run once to set up the Python environment and install dependencies
    ./run_dev.sh # Starts the backend on http://localhost:8000
    ```
    Keep this terminal running.
4.  **Set up and run the Frontend:**
    Open a new terminal.
    ```bash
    cd frontend/chat-ui
    ./setup.sh  # Run once to install Node.js dependencies
    ./run_dev.sh # Starts the frontend, typically on http://localhost:5173
    ```
    Keep this terminal running.
5.  **Access the application:**
    *   Backend API: `http://localhost:8000`
    *   Frontend UI: `http://localhost:5173` (or as indicated by Vite)

## How to Use

1.  Open the frontend URL (e.g., `http://localhost:5173`) in your web browser.
2.  Upload documents using the file input field or by dragging and dropping files onto the designated area.
3.  The application will show the upload progress and a status message upon completion.
4.  Once a document is processed, a message will appear in the chat indicating it's ready.
5.  Type your questions about the document's content into the chat input field and press Enter or click "Send".
6.  The LLM's response, along with sources from the document, will be streamed to the chat interface.
7.  Your chat history is automatically saved in your browser's `localStorage`.
8.  You can clear the current chat history using the "Clear Chat" button in the header.

## Key Technologies Used

*   **Backend:**
    *   FastAPI: High-performance Python web framework.
    *   Langchain: Framework for developing applications powered by LLMs.
    *   ChromaDB: Open-source embedding database.
    *   Ollama: For running local LLMs.
    *   Sentence-Transformers: For generating text embeddings.
    *   PyPDF2, python-docx, Markdown, BeautifulSoup4, Pandas: For parsing various file types.
    *   Uvicorn: ASGI server for FastAPI.
*   **Frontend:**
    *   React: JavaScript library for building user interfaces.
    *   Vite: Fast frontend build tool.
    *   Tailwind CSS: Utility-first CSS framework.
    *   Axios: For file uploads (HTTP client).
    *   Fetch API: For streaming chat responses.
*   **General:**
    *   Python
    *   JavaScript

## (Optional) Future Enhancements

*   **Support for More File Types:** Expand parsing capabilities (e.g., `.pptx`, images with OCR).
*   **User Accounts & Authentication:** Secure access and manage user-specific documents/history.
*   **Configurable Models from UI:** Allow users to select LLM and embedding models via the interface.
*   **Advanced RAG Strategies:** Implement re-ranking of retrieved documents, query transformations.
*   **Metadata Filtering:** Allow users to filter documents or search within specific metadata.
*   **Deployment Scripts:** Dockerize the application for easier deployment.
*   **Enhanced Error Handling:** More granular error messages and recovery options.
*   **UI for Model Management:** Interface to see available Ollama models or select embedding models for upload.
*   **Session Management:** Persist selected embedding models or other settings per session.
