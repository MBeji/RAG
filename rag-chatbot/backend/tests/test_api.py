import pytest
import os
import io
import json
from fastapi.testclient import TestClient

# Adjust the import according to your application structure
# This assumes your FastAPI app instance is named 'app' in 'backend/app/main.py'
# And that tests are run from the 'backend' directory.
# To ensure this works when running pytest from `rag-chatbot/backend/`,
# we might need to ensure the 'app' directory (containing main.py) is recognized.
# Pytest usually handles this by adding the current working directory to sys.path.
from app.main import app 

@pytest.fixture(scope="module")
def client():
    # Before creating TestClient, ensure necessary directories exist if app creation touches them
    # e.g., DATA_DIR or VECTOR_DB_PATH if created on startup (our app creates them lazily)
    # For tests, it's also good to ensure that any persistent paths (like VECTOR_DB_PATH)
    # are configured to point to temporary test-specific locations if possible,
    # or that cleanup occurs. For this example, we assume the default paths are used
    # and tests either mock out DB interactions or are okay with using the dev DB path.
    with TestClient(app) as c:
        yield c

# --- /upload Endpoint Tests ---
def test_upload_txt_file_success(client: TestClient):
    # Create a dummy txt file for upload
    dummy_txt_content = b"This is a test text file for API upload."
    # When sending a file, FastAPI expects a tuple: (filename, file-like-object, content_type)
    file_data = {"file": ("test_upload.txt", io.BytesIO(dummy_txt_content), "text/plain")}
    
    response = client.post("/upload", files=file_data) # 'files' keyword arg for TestClient
    
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["filename"] == "test_upload.txt"
    assert "total_chunks" in response_json
    # Check for default embedding model as per current /upload endpoint
    assert response_json["embedding_model_name"] == "all-MiniLM-L6-v2" 

def test_upload_unsupported_file_type(client: TestClient):
    dummy_content = b"Some unsupported content."
    file_data = {"file": ("test_upload.exe", io.BytesIO(dummy_content), "application/octet-stream")}
    
    response = client.post("/upload", files=file_data)
    assert response.status_code == 400
    assert "File type not allowed" in response.json()["detail"]

def test_upload_no_file(client: TestClient):
    # Test by not providing the 'file' part in the multipart request
    response = client.post("/upload") # No 'files' argument
    assert response.status_code == 422 # FastAPI's validation error for missing File parameter

# --- /chat Endpoint Tests ---

@pytest.fixture(scope="function") # Function scope to re-apply mocks for each test
def mock_chat_dependencies(mocker): # mocker is a pytest-mock fixture
    # Mock query_vector_store from app.main module
    mocker.patch(
        "app.main.query_vector_store", # Path to the function in the module where it's USED
        return_value={
            "documents": [["Mocked context from document."]],
            "metadatas": [[{"source": "mock_doc.txt", "chunk_num": 0, "embedding_model": "all-MiniLM-L6-v2"}]],
            "distances": [[0.1]]
        }
    )
    # Mock get_llm_response_stream from app.main module
    def mock_stream_generator(*args, **kwargs):
        # Yield data in the format expected by the chat_response_generator (SSE events)
        yield "Mocked " # This will be wrapped into data: {"type": "token", "data": "Mocked "} by chat_response_generator
        yield "LLM "
        yield "response."
    # We are mocking the function that get_llm_response_stream is imported AS in app.main
    mocker.patch("app.main.get_llm_response_stream", side_effect=mock_stream_generator)


def test_chat_streaming_success(client: TestClient, mock_chat_dependencies):
    payload = {"query": "What is this about?"} # Uses default embedding model
    
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    
    stream_content = response.text 
    events = stream_content.strip().split("\n\n")
    
    # Expected events based on mocks and chat_response_generator structure
    # 1. Sources event
    # 2. Token events (3 from mock_stream_generator)
    # 3. End event
    assert len(events) == 1 + 3 + 1 # sources + 3 tokens + end

    # Check sources event
    event1_data = json.loads(events[0].replace("data: ", ""))
    assert event1_data["type"] == "sources"
    assert len(event1_data["data"]) == 1
    assert event1_data["data"][0]["source_file"] == "mock_doc.txt"

    # Check token events (simplified check for content)
    event2_data = json.loads(events[1].replace("data: ", ""))
    assert event2_data["type"] == "token"
    assert event2_data["data"] == "Mocked "
    
    event3_data = json.loads(events[2].replace("data: ", ""))
    assert event3_data["type"] == "token"
    assert event3_data["data"] == "LLM "

    event4_data = json.loads(events[3].replace("data: ", ""))
    assert event4_data["type"] == "token"
    assert event4_data["data"] == "response."

    # Check end event
    event5_data = json.loads(events[4].replace("data: ", ""))
    assert event5_data["type"] == "end"
    assert event5_data["data"] == "Stream finished."


def test_chat_empty_query(client: TestClient):
    response = client.post("/chat", json={"query": ""}) 
    # The endpoint itself has: if not chat_query.query: raise HTTPException(...)
    # This check is hit before Pydantic validation for an empty string if not for Pydantic's own rules.
    # FastAPI/Pydantic should return 422 if field validation fails (e.g. if query had MinLength)
    # but the current explicit check in the endpoint returns 400.
    assert response.status_code == 400 
    assert "Query parameter 'query' is required" in response.json()["detail"]

def test_chat_no_documents_found(client: TestClient, mocker):
    # Mock query_vector_store to return no documents
    mocker.patch(
        "app.main.query_vector_store",
        return_value={"documents": [[]], "metadatas": [[]], "distances": [[]]} # Empty results
    )
    
    payload = {"query": "Query for non-existent info"}
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 200 # Still 200, but stream contains an error-type event
    assert response.headers["content-type"] == "text/event-stream"
    
    stream_content = response.text
    events = stream_content.strip().split("\n\n")
    
    assert len(events) == 1 # Only one event, the "no_docs_message"
    event_data = json.loads(events[0].replace("data: ", ""))
    assert event_data["type"] == "error"
    assert "I could not find any documents relevant enough" in event_data["data"]["llm_response"]

# Note for running tests:
# 1. Navigate to the `rag-chatbot/backend/` directory.
# 2. Activate your Python virtual environment (e.g., `source .venv/bin/activate`).
# 3. Run pytest: `pytest` or `python -m pytest`.
# These tests should not require Ollama to be running due to mocking.
```
