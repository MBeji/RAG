from langchain_community.llms import Ollama
from typing import Iterator # Import Iterator

DEFAULT_MODEL = "llama2" 

# New streaming function
def get_llm_response_stream(prompt_str: str, model_name: str = DEFAULT_MODEL) -> Iterator[str]:
    """
    Gets a streamed response from a local Ollama LLM.
    Args:
        prompt_str: The complete prompt to send to the LLM.
        model_name: The name of the Ollama model to use.
    Yields:
        str: Chunks of the LLM's response.
    Raises:
        Exception: If there's an error interacting with Ollama.
    """
    try:
        llm = Ollama(model=model_name)
        for chunk in llm.stream(prompt_str):
            yield chunk
    except Exception as e:
        error_message = f"Error interacting with Ollama model '{model_name}' for streaming: {e}. "                         f"Please ensure Ollama is running and the model '{model_name}' is pulled."
        print(error_message)
        raise # Re-raise the exception to be caught by the endpoint

# Existing non-streaming function (can be kept or removed based on need)
def get_llm_response(prompt_str: str, model_name: str = DEFAULT_MODEL) -> str:
    try:
        llm = Ollama(model=model_name)
        response = llm.invoke(prompt_str)
        return response
    except Exception as e:
        error_message = f"Error interacting with Ollama model '{model_name}': {e}. "                         f"Please ensure Ollama is running and the model '{model_name}' is pulled. "
        print(error_message)
        return error_message
