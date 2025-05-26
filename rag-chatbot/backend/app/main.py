"""
Main FastAPI application for the RAG Chatbot.

This application provides API endpoints for:
- Uploading documents for processing and ingestion into a vector store.
- Querying the vector store directly (for debugging or specific use cases).
- Chatting with an LLM using a RAG approach, with responses streamed back to the client.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator 
import json 
import shutil
import os
from werkzeug.utils import secure_filename # Import secure_filename

# Relative imports for modules within the backend package
from ..utils.parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    extract_text_from_md,
    extract_text_from_csv
)
from ..utils.chunking import chunk_text
from ..vector_store.chroma_db import (
    add_documents_to_store, 
    query_vector_store, 
    DEFAULT_EMBEDDING_MODEL
)
# Streaming LLM function is primary for chat; non-streaming can be removed if not used elsewhere.
from ..models.llm import get_llm_response_stream
# from ..models.llm import get_llm_response # Removed as non-streaming chat is not primary

# Define the directory for storing uploaded files, relative to this main.py file.
# backend/app/main.py -> ../../data
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True) # Ensure the data directory exists on startup

app = FastAPI(
    title="RAG Chatbot API",
    description="API for document upload, vector store interaction, and RAG-based chat.",
    version="1.0.0"
)

# Dictionary mapping file extensions to their respective text extraction functions.
ALLOWED_EXTENSIONS = {
    ".pdf": extract_text_from_pdf,
    ".txt": extract_text_from_txt,
    ".docx": extract_text_from_docx,
    ".md": extract_text_from_md,
    ".csv": extract_text_from_csv,
}

@app.post("/upload", summary="Upload a document for processing")
async def upload_file(
    file: UploadFile = File(
        ..., 
        description="The document file to upload.",
        # Example: Set a max file size of 25MB
        # max_size=25 * 1024 * 1024 
        # For Starlette/FastAPI, max_size on UploadFile is not directly supported.
        # File size limits are typically handled by the web server (e.g., Nginx, Uvicorn --limit-max-request-size)
        # or by checking file.size after upload starts, or with custom middleware.
        # For this example, we'll proceed without direct `max_size` in `File()`
        # but will add a check for file.size manually if possible after initial save,
        # or rely on server limits. Let's assume server limit for now and focus on filename.
    ),
    embedding_model_name: str = Form(DEFAULT_EMBEDDING_MODEL, description="Name of the sentence-transformer model for embeddings.")
):
    """
    Handles document uploads. The file is saved (with a sanitized filename), 
    its text is extracted, chunked, and then added to the vector store 
    using the specified embedding model.
    """
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{file_extension}' not allowed. Allowed types are: {', '.join(ALLOWED_EXTENSIONS.keys())}")

    # Sanitize the filename to prevent path traversal and other attacks
    safe_filename = secure_filename(file.filename)
    if not safe_filename: # Handle cases where filename might be empty or only unsafe characters
        safe_filename = "uploaded_file" + file_extension # Fallback filename

    file_path = os.path.join(DATA_DIR, safe_filename)
    
    try:
        # Save the uploaded file to the DATA_DIR
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        # Ensure the uploaded file object is closed
        if hasattr(file, 'file') and not file.file.closed:
            file.file.close()

    try:
        # 1. Extract text from the saved file
        extraction_func = ALLOWED_EXTENSIONS[file_extension]
        extracted_text = extraction_func(file_path)
        if not extracted_text:
            # If no text, no point proceeding. File remains in DATA_DIR.
            return {"message": f"File '{safe_filename}' uploaded, but no text could be extracted. Nothing added to vector store."}

        # 2. Chunk the extracted text
        file_is_markdown = file_extension == ".md"
        chunks = chunk_text(extracted_text, is_markdown=file_is_markdown) 
        if not chunks:
            return {"message": f"File '{safe_filename}' processed, but no chunks were generated (text might be too short or empty). Nothing added to vector store."}

        # 3. Prepare metadata and IDs for vector store
        metadatas = [{"source": safe_filename, "chunk_num": i} for i, _ in enumerate(chunks)]
        # IDs are generated by chroma_db.py if not provided, but we can create base IDs here.
        # The add_documents_to_store function will make them unique per collection.
        ids = [f"{safe_filename}_chunk_{i}" for i, _ in enumerate(chunks)] 

        # 4. Add text chunks, metadatas, and IDs to the vector store
        add_documents_to_store(
            text_chunks=chunks, 
            metadatas=metadatas, 
            ids=ids, # Pass base IDs
            embedding_model_name=embedding_model_name
        )
        
        return {
            "message": f"File '{safe_filename}' processed with embedding model '{embedding_model_name}' and added to vector store.",
            "filename": safe_filename, # Return the sanitized filename
            "total_chunks": len(chunks),
            "embedding_model_name": embedding_model_name
        }
    except Exception as e:
        # If any error occurs during processing after file save, attempt to clean up the saved file.
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned up file {file_path} after processing error.")
            except Exception as remove_e:
                # Log this failure but prioritize the original processing error.
                print(f"Failed to remove file {file_path} during error cleanup: {remove_e}")
        raise HTTPException(status_code=500, detail=f"Error processing file '{safe_filename}': {e}")


@app.get("/query", summary="Query the vector store directly (for debugging/testing)")
async def query_documents(q: str = None, embedding_model: Optional[str] = DEFAULT_EMBEDDING_MODEL, top_k: int = 5):
    """
    Performs a direct similarity search in the vector store for a given query text.
    Mainly intended for debugging or testing the vector store.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    try:
        results = query_vector_store(
            query_text=q, 
            top_k=top_k,
            embedding_model_name=embedding_model # Use the specified or default embedding model
        )
        if not results or not results.get('documents') or not results['documents'][0]:
             return {"message": "No relevant documents found for your query.", "query": q, "results": results, "embedding_model_used": embedding_model}
        return {"query": q, "results": results, "embedding_model_used": embedding_model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying vector store: {e}")


class ChatQuery(BaseModel):
    """
    Pydantic model for the request body of the /chat endpoint.
    """
    query: str = Field(..., description="The user's query to the chatbot.")
    top_k: int = Field(3, description="Number of document chunks to retrieve for context.", gt=0, le=10)
    model_name: str = Field("llama2", description="Name of the Ollama LLM model to use for generation.")
    embedding_model_name: str = Field(DEFAULT_EMBEDDING_MODEL, description="Name of the embedding model used for document retrieval.")
    relevance_score_threshold: Optional[float] = Field(None, description="Optional L2 distance threshold for filtering retrieved documents (lower is better). E.g., 1.0.")

async def chat_response_generator(chat_query: ChatQuery) -> AsyncGenerator[str, None]:
    """
    Asynchronously generates Server-Sent Events (SSE) for a chat response.

    This generator performs the RAG pipeline:
    1. Retrieves relevant document chunks from the vector store.
    2. If no relevant documents are found, sends an error event.
    3. Sends a 'sources' event with metadata of retrieved documents.
    4. Constructs a prompt using the query and context.
    5. Streams tokens from the LLM as 'token' events.
    6. Sends an 'end' event when the LLM stream finishes.
    7. Sends an 'error' event if any exception occurs during the process.
    """
    user_query = chat_query.query
    top_k_retrieval = chat_query.top_k
    llm_model_name = chat_query.model_name
    embedding_model_name_for_query = chat_query.embedding_model_name
    relevance_threshold_for_query = chat_query.relevance_score_threshold

    try:
        # Step 1: Retrieve relevant documents from the vector store
        retrieved_results = query_vector_store(
            query_text=user_query,
            top_k=top_k_retrieval,
            embedding_model_name=embedding_model_name_for_query,
            relevance_score_threshold=relevance_threshold_for_query
        )
        
        documents = retrieved_results.get('documents', [[]])[0]
        metadatas = retrieved_results.get('metadatas', [[]])[0]
        distances = retrieved_results.get('distances', [[]])[0]

        # Step 2: Handle case where no documents are found or pass the threshold
        if not documents:
            no_docs_message = {
                "type": "error", # Custom event type for client to handle
                "data": {
                    "llm_response": f"I could not find any documents relevant enough (threshold: {relevance_threshold_for_query}, model: '{embedding_model_name_for_query}') to answer your query. Try adjusting the threshold or uploading more relevant documents.",
                    "sources": [],
                }
            }
            yield f"data: {json.dumps(no_docs_message)}\n\n"
            return # Stop generation if no documents

        # Step 3: Send retrieved sources to the client
        sources_for_response = []
        if metadatas:
            for i in range(len(documents)):
                meta = metadatas[i]
                dist = distances[i] if i < len(distances) else None
                source_info = {
                    "source_file": meta.get("source", "Unknown source"),
                    "chunk_number": meta.get("chunk_num", "N/A"),
                    "embedding_model": meta.get("embedding_model", embedding_model_name_for_query),
                    "distance": dist
                }
                sources_for_response.append(source_info)
        
        sources_event = {"type": "sources", "data": sources_for_response}
        yield f"data: {json.dumps(sources_event)}\n\n"

        # Step 4: Construct the prompt for the LLM
        context_str = "\n---\n".join(documents)
        prompt = f"""Based on the following context (retrieved using embedding model '{embedding_model_name_for_query}' and relevance threshold {relevance_threshold_for_query if relevance_threshold_for_query is not None else 'N/A'}), please answer the query. If the context does not provide enough information, clearly state that. Do not use any external knowledge beyond the provided context.

Context:
---
{context_str}
---

Query: {user_query}"""
        
        # Step 5: Stream tokens from the LLM
        for token_chunk in get_llm_response_stream(prompt_str=prompt, model_name=llm_model_name):
            token_event = {"type": "token", "data": token_chunk}
            yield f"data: {json.dumps(token_event)}\n\n"
        
        # Step 6: Send an end-of-stream signal
        end_event = {"type": "end", "data": "Stream finished."}
        yield f"data: {json.dumps(end_event)}\n\n"

    except Exception as e:
        # Step 7: Handle any exceptions and send an error event
        print(f"Error in chat_response_generator for query '{user_query}': {e}")
        error_response_data = {"llm_response": f"Sorry, an error occurred while processing your chat request: {str(e)}", "sources": []}
        if "Error interacting with Ollama" in str(e):
            error_response_data["llm_response"] = f"Ollama interaction error: {str(e)}. Please ensure Ollama is running and the model '{llm_model_name}' is available."
        
        error_event = {"type": "error", "data": error_response_data}
        yield f"data: {json.dumps(error_event)}\n\n"


@app.post("/chat", summary="Chat with the RAG model (streaming response)")
async def chat_with_rag_streaming(chat_query: ChatQuery):
    """
    Handles chat requests using Retrieval Augmented Generation (RAG).
    The response is streamed back to the client as Server-Sent Events (SSE).

    SSE Events:
    - `sources`: Contains a list of source documents used for context.
    - `token`: Contains a token of the LLM's generated response.
    - `end`: Signals the end of the LLM response stream.
    - `error`: Signals an error (either no documents found or an exception occurred).
    """
    if not chat_query.query: # Basic validation
        raise HTTPException(status_code=400, detail="Query parameter 'query' is required in the request body.")
    
    return StreamingResponse(chat_response_generator(chat_query), media_type="text/event-stream")

# To run this (from backend directory):
# uvicorn app.main:app --reload --port 8000
# Example usage from browser JS or curl:
# curl -N -X POST "http://localhost:8000/chat" \
#      -H "Content-Type: application/json" \
#      -d '{"query":"What is ChromaDB?"}'
```
