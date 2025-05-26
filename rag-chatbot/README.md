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

## Setup Instructions

### Prerequisites

*   **Node.js and npm:** For the frontend. (Download from [nodejs.org](https://nodejs.org/))
*   **Python 3.8+ and pip:** For the backend. (Download from [python.org](https://www.python.org/))
*   **Ollama:** Installed and running. (Download and instructions: [https://ollama.com](https://ollama.com))
*   **Ollama Model(s):** At least one model pulled. Examples:
    *   `ollama pull llama2`
    *   `ollama pull mistral`
    *   `ollama pull all-minilm` (for embeddings, though the app uses sentence-transformers library directly)

### Backend Setup

1.  **Navigate to the `backend` directory:**
    ```bash
    cd backend
    ```
2.  **Create a Python virtual environment:**
    ```bash
    python -m venv .venv
    ```
3.  **Activate the virtual environment:**
    *   **Windows:**
        ```bash
        .venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Frontend Setup

1.  **Navigate to the frontend project directory** (from the project root):
    ```bash
    cd frontend/chat-ui
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```

## Running the Application

Ensure all prerequisites are met and setup steps are completed.

**1. Start Ollama:**
*   Make sure your Ollama application is running. On some systems, it runs as a background service after installation. If not, you might need to start it manually (e.g., `ollama serve` in a separate terminal, depending on your OS and Ollama version).
*   Verify that you have at least one model available by running:
    ```bash
    ollama list
    ```

**2. Start the Backend:**
*   Navigate to the `backend` directory (if not already there).
*   Activate your Python virtual environment (if not already active).
*   Run the FastAPI server:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
*   The backend API will be available at `http://localhost:8000`. You should see a message like "Application startup complete."

**3. Start the Frontend:**
*   Navigate to the `frontend/chat-ui` directory (if not already there).
*   Run the Vite development server:
    ```bash
    npm run dev
    ```
*   The frontend application will typically be available at `http://localhost:5173`. Vite will indicate the exact URL if port 5173 is busy.

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
