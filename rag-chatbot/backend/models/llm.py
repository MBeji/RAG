"""
Module for interacting with local Large Language Models (LLMs) via Ollama.

Provides both streaming and non-streaming functions to get responses from
specified Ollama models. It includes error handling for Ollama interactions.
"""
from langchain_community.llms import Ollama
from typing import Iterator 

# Default Ollama model to use if not specified by the caller.
DEFAULT_MODEL = "llama2" 

def get_llm_response_stream(prompt_str: str, model_name: str = DEFAULT_MODEL) -> Iterator[str]:
    """
    Gets a streamed response from a local Ollama LLM.

    Args:
        prompt_str: The complete prompt to send to the LLM.
        model_name: The name of the Ollama model to use (e.g., 'llama2', 'mistral').
                    Ensure this model is available in your local Ollama setup.

    Yields:
        str: Chunks of the LLM's response as they are generated.

    Raises:
        Exception: If an error occurs during interaction with the Ollama model.
                   The caller is responsible for handling this exception.
    """
    try:
        llm = Ollama(model=model_name)
        # The stream method returns an iterator of response chunks.
        for chunk in llm.stream(prompt_str):
            yield chunk
    except Exception as e:
        error_message = (
            f"Error interacting with Ollama model '{model_name}' for streaming: {e}. "
            f"Please ensure Ollama is running and the model '{model_name}' is pulled. "
            f"You can pull a model using 'ollama pull {model_name}'."
        )
        print(error_message) # Log for server visibility
        raise # Re-raise the exception to be caught by the API endpoint

def get_llm_response(prompt_str: str, model_name: str = DEFAULT_MODEL) -> str:
    """
    Gets a non-streamed (complete) response from a local Ollama LLM.

    Args:
        prompt_str: The complete prompt to send to the LLM.
        model_name: The name of the Ollama model to use (e.g., 'llama2', 'mistral').
                    Ensure this model is available in your local Ollama setup.

    Returns:
        str: The LLM's complete response as a string.
             If an error occurs, a descriptive error message string is returned instead.
    """
    try:
        llm = Ollama(model=model_name)
        response = llm.invoke(prompt_str)
        return response
    except Exception as e:
        error_message = (
            f"Error interacting with Ollama model '{model_name}': {e}. "
            f"Please ensure Ollama is running and the model '{model_name}' is pulled. "
            f"You can pull a model using 'ollama pull {model_name}'."
        )
        print(error_message) # Log for server visibility
        # For non-streaming, returning the error message string can be handled by callers
        # that expect a direct string response (e.g., older or simpler API endpoints).
        return error_message

# Example Usage (optional, for local testing and demonstration)
if __name__ == '__main__':
    print(f"--- Testing Non-Streaming LLM ({DEFAULT_MODEL}) ---")
    test_prompt = "Explain the concept of a black hole in simple terms."
    # Ensure Ollama is running and the DEFAULT_MODEL is pulled (e.g., 'ollama pull llama2')
    
    print(f"Sending prompt: '{test_prompt}'")
    non_stream_response = get_llm_response(test_prompt)
    print(f"Non-Streaming Response:\n{non_stream_response}\n")

    print(f"--- Testing Streaming LLM ({DEFAULT_MODEL}) ---")
    print(f"Streaming Response for prompt: '{test_prompt}'")
    try:
        full_streamed_response = []
        for i, token in enumerate(get_llm_response_stream(test_prompt)):
            print(token, end="", flush=True)
            full_streamed_response.append(token)
            # Example: Stop after a certain number of tokens or a newline for brevity in test output
            if i > 70 and "\n" in token: 
                print("\n... (truncated stream for example display)")
                break
        print("\n--- Stream Test Complete ---\n")
        # print(f"Full streamed response assembled: {''.join(full_streamed_response)}")
    except Exception as e:
        print(f"\nError during streaming test: {e}")

    # Example of testing with a (potentially) non-existent model to see error handling
    # print("\n--- Testing with a Non-Existent Model (non-streaming) ---")
    # error_response_non_stream = get_llm_response(test_prompt, model_name="this_model_does_not_exist_12345")
    # print(f"LLM Error Response (Non-Streaming):\n{error_response_non_stream}")

    # print("\n--- Testing with a Non-Existent Model (streaming) ---")
    # try:
    #     print(f"Streaming response for '{test_prompt}' with non-existent model:")
    #     for token in get_llm_response_stream(test_prompt, model_name="this_model_does_not_exist_12345"):
    #         print(token, end="", flush=True)
    #     print()
    # except Exception as e:
    #     print(f"\nLLM Error (Streaming):\n{e}")
    pass
