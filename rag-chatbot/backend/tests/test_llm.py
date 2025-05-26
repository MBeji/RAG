import pytest
from unittest.mock import patch, MagicMock

# Adjust the import path according to your project structure
# This assumes that 'models' is a package and 'llm' is a module within it.
# If running pytest from 'rag-chatbot/backend/', this path should work.
from models.llm import get_llm_response_stream, get_llm_response, DEFAULT_MODEL

# --- Tests for get_llm_response_stream ---

@patch('models.llm.Ollama') # Mocking Ollama where it's used in llm.py
def test_get_llm_response_stream_success(mock_ollama_class):
    # Configure the mock Ollama instance and its stream method
    mock_ollama_instance = MagicMock()
    mock_ollama_instance.stream.return_value = iter(["Test ", "response ", "streamed."])
    mock_ollama_class.return_value = mock_ollama_instance

    prompt = "Test prompt"
    response_chunks = []
    for chunk in get_llm_response_stream(prompt):
        response_chunks.append(chunk)

    assert "".join(response_chunks) == "Test response streamed."
    mock_ollama_instance.stream.assert_called_once_with(prompt)
    mock_ollama_class.assert_called_once_with(model=DEFAULT_MODEL)

@patch('models.llm.Ollama')
def test_get_llm_response_stream_ollama_error(mock_ollama_class):
    # Configure the mock Ollama instance to raise an exception
    mock_ollama_instance = MagicMock()
    mock_ollama_instance.stream.side_effect = Exception("Ollama API error")
    mock_ollama_class.return_value = mock_ollama_instance

    prompt = "Test prompt for error"
    with pytest.raises(Exception, match="Ollama API error"):
        # Consume the generator to trigger the exception
        list(get_llm_response_stream(prompt))
    
    mock_ollama_instance.stream.assert_called_once_with(prompt)

@patch('models.llm.Ollama')
def test_get_llm_response_stream_empty_prompt(mock_ollama_class):
    # Configure the mock Ollama instance for an empty prompt
    mock_ollama_instance = MagicMock()
    # Define what streaming an empty prompt should return, e.g., an empty iterator or specific behavior
    mock_ollama_instance.stream.return_value = iter([]) # Or iter(["Empty prompt response"])
    mock_ollama_class.return_value = mock_ollama_instance

    prompt = "" # Empty prompt
    response_chunks = list(get_llm_response_stream(prompt))

    # Assert based on expected behavior for empty prompts
    # For example, if it's expected to return an empty list of chunks:
    assert response_chunks == [] 
    # Or if it processes it and returns a canned response:
    # assert "".join(response_chunks) == "Empty prompt response"

    mock_ollama_instance.stream.assert_called_once_with(prompt)

# --- Add tests for get_llm_response function here ---

@patch('models.llm.Ollama')
def test_get_llm_response_success(mock_ollama_class):
    mock_ollama_instance = MagicMock()
    mock_ollama_instance.invoke.return_value = "Test response non-streamed."
    mock_ollama_class.return_value = mock_ollama_instance

    prompt = "Test prompt non-streamed"
    response = get_llm_response(prompt)

    assert response == "Test response non-streamed."
    mock_ollama_instance.invoke.assert_called_once_with(prompt)
    mock_ollama_class.assert_called_once_with(model=DEFAULT_MODEL)

@patch('models.llm.Ollama')
def test_get_llm_response_ollama_error(mock_ollama_class):
    mock_ollama_instance = MagicMock()
    mock_ollama_instance.invoke.side_effect = Exception("Ollama API error non-streamed")
    mock_ollama_class.return_value = mock_ollama_instance

    prompt = "Test prompt for non-streamed error"
    # The current get_llm_response returns an error message string, not an exception
    response = get_llm_response(prompt)
    
    assert "Error interacting with Ollama model" in response
    assert "Ollama API error non-streamed" in response
    mock_ollama_instance.invoke.assert_called_once_with(prompt)

@patch('models.llm.Ollama')
def test_get_llm_response_empty_prompt(mock_ollama_class):
    mock_ollama_instance = MagicMock()
    mock_ollama_instance.invoke.return_value = "Empty prompt non-streamed response"
    mock_ollama_class.return_value = mock_ollama_instance

    prompt = "" # Empty prompt
    response = get_llm_response(prompt)

    assert response == "Empty prompt non-streamed response"
    mock_ollama_instance.invoke.assert_called_once_with(prompt)
