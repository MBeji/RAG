from fastapi import FastAPI, File, UploadFile, HTTPException, Form # Added Form
import shutil
import os

# Adjust import paths based on actual structure if backend/app/main.py
# Assuming main.py is in backend/app/
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
    DEFAULT_EMBEDDING_MODEL # Import the default model name
)

# Create the data directory if it doesn't exist (relative to this main.py file)
# backend/app/main.py -> ../../data
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI()

ALLOWED_EXTENSIONS = {
    ".pdf": extract_text_from_pdf,
    ".txt": extract_text_from_txt,
    ".docx": extract_text_from_docx,
    ".md": extract_text_from_md,
    ".csv": extract_text_from_csv,
}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    embedding_model_name: str = Form(DEFAULT_EMBEDDING_MODEL) # Added form field for model name
):
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types are: {', '.join(ALLOWED_EXTENSIONS.keys())}")

    file_path = os.path.join(DATA_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        # Ensure file is closed if saving fails
        file.file.close()
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        # Important: Ensure the file is closed regardless of success or failure during saving.
        # If the file object was already closed by shutil.copyfileobj or an earlier close,
        # this might raise an error on an already closed file, so handle that.
        if not file.file.closed:
            file.file.close()

    try:
        # 1. Extract text
        extraction_func = ALLOWED_EXTENSIONS[file_extension]
        extracted_text = extraction_func(file_path)
        if not extracted_text:
            # If no text is extracted, it's not necessarily an error that should halt everything,
            # but we should inform the user and not proceed with chunking/storage.
            # No cleanup of the file is needed here as it was successfully uploaded.
            return {"message": f"File '{file.filename}' uploaded, but no text could be extracted. Nothing added to vector store."}

        # 2. Chunk text
        file_is_markdown = file_extension == ".md"
        chunks = chunk_text(extracted_text, is_markdown=file_is_markdown) # Pass the flag
        if not chunks:
            # If no chunks are generated (e.g., text is too short or empty after extraction)
            return {"message": f"File '{file.filename}' processed, but no chunks were generated (text might be too short or empty). Nothing added to vector store."}

        # 3. Prepare metadata and IDs for vector store
        metadatas = [{"source": file.filename, "chunk_num": i} for i, _ in enumerate(chunks)]
        ids = [f"{file.filename}_chunk_{i}" for i, _ in enumerate(chunks)] # Base IDs

        # 4. Add to vector store, passing the embedding_model_name
        add_documents_to_store(
            text_chunks=chunks, 
            metadatas=metadatas, 
            ids=ids,
            embedding_model_name=embedding_model_name # Pass it here
        )
        
        return {
            "message": f"File '{file.filename}' processed with embedding model '{embedding_model_name}' and added to vector store.",
            "filename": file.filename,
            "total_chunks": len(chunks),
            "embedding_model_name": embedding_model_name
        }
    except Exception as e:
        # This catches errors from extraction, chunking, or adding to store
        # Clean up the saved file if processing fails at any of these stages
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as remove_e:
                # Log this failure or handle it; for now, we prioritize the original error.
                print(f"Failed to remove file {file_path} during error cleanup: {remove_e}")
        raise HTTPException(status_code=500, detail=f"Error processing file '{file.filename}': {e}")

# To run this (from backend directory):
# uvicorn app.main:app --reload --port 8000

from ..vector_store.chroma_db import query_vector_store # Ensure this import is added

# ... (existing /upload endpoint) ...

@app.get("/query")
async def query_documents(q: str = None):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    
    try:
        results = query_vector_store(query_text=q, top_k=5) # Using default top_k=5
        # The results from ChromaDB typically include: ids, documents, metadatas, distances
        # For example:
        # {
        #    'ids': [['id1', 'id2']],
        #    'documents': [['doc text 1', 'doc text 2']],
        #    'metadatas': [[{'source': 'file1'}, {'source': 'file2'}]],
        #    'distances': [[0.1, 0.2]]
        # }
        # We can return this directly or simplify it if needed.
        # For now, returning the direct result.
        
        # Check if results are structured as expected and not empty
        if not results or not results.get('documents') or not results['documents'][0]:
             return {"message": "No relevant documents found for your query.", "query": q, "results": results}

        return {"query": q, "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying vector store: {e}")


from ..models.llm import get_llm_response
from pydantic import BaseModel, Field # Ensure Field is imported if using it for defaults, though not strictly needed for None
from typing import Optional # For Optional fields

# ... (existing /upload and /query endpoints) ...

class ChatQuery(BaseModel):
    query: str
    top_k: int = 3
    model_name: str = "llama2" # LLM model
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL
    relevance_score_threshold: Optional[float] = None # Added, e.g. 1.0 for L2 distance

@app.post("/chat")
async def chat_with_rag(chat_query: ChatQuery):
    user_query = chat_query.query
    top_k_retrieval = chat_query.top_k
    llm_model_name = chat_query.model_name
    embedding_model_name_for_query = chat_query.embedding_model_name
    relevance_threshold_for_query = chat_query.relevance_score_threshold # Get from request

    if not user_query:
        raise HTTPException(status_code=400, detail="Query parameter 'query' is required in the request body.")

    try:
        # 1. Retrieve relevant documents
        retrieved_results = query_vector_store(
            query_text=user_query, 
            top_k=top_k_retrieval,
            embedding_model_name=embedding_model_name_for_query,
            relevance_score_threshold=relevance_threshold_for_query # Pass it here
        )
        
        documents = retrieved_results.get('documents', [[]])[0]
        metadatas = retrieved_results.get('metadatas', [[]])[0]
        distances = retrieved_results.get('distances', [[]])[0] # Get distances for response

        if not documents:
            return {
                "llm_response": f"I could not find any documents relevant enough (threshold: {relevance_threshold_for_query}, model: '{embedding_model_name_for_query}') to answer your query.",
                "sources": [],
                "embedding_model_used": embedding_model_name_for_query,
                "relevance_threshold_used": relevance_threshold_for_query
            }

        context_str = "\n---\n".join(documents)
        prompt = f"""Based on the following context (retrieved using embedding model '{embedding_model_name_for_query}' and relevance threshold {relevance_threshold_for_query}), please answer the query. If the context does not provide enough information, clearly state that. Do not use any external knowledge beyond the provided context.

Context:
---
{context_str}
---

Query: {user_query}"""

        # 3. Generate - Get response from LLM
        llm_answer = get_llm_response(prompt_str=prompt, model_name=llm_model_name)

        # Check if LLM interaction itself returned an error message (as per get_llm_response design)
        if "Error interacting with Ollama" in llm_answer:
            # Consider logging the full llm_answer for debugging on the server
            print(f"Ollama interaction error for query '{user_query}': {llm_answer}")
            raise HTTPException(status_code=503, detail=llm_answer)


        
        llm_answer = get_llm_response(prompt_str=prompt, model_name=llm_model_name)
        
        sources_for_response = []
        if metadatas: # Should have same length as documents and distances
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
        
        return {
            "llm_response": llm_answer,
            "sources": sources_for_response,
            "embedding_model_used": embedding_model_name_for_query,
            "relevance_threshold_used": relevance_threshold_for_query
        }

    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        if "Error interacting with Ollama" in str(e):
             raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Error processing chat query: {e}")
