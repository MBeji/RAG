from langchain_community.llms import Ollama # Updated import for newer Langchain versions

# It's good practice to specify a model.
# User must have Ollama installed and the model pulled, e.g., 'ollama pull llama2'
DEFAULT_MODEL = "llama2" 

def get_llm_response(prompt_str: str, model_name: str = DEFAULT_MODEL) -> str:
    """
    Gets a response from a local Ollama LLM.

    Args:
        prompt_str: The complete prompt to send to the LLM.
        model_name: The name of the Ollama model to use (e.g., 'llama2', 'mistral').
                    Ensure this model is available in your local Ollama setup.

    Returns:
        The LLM's response as a string.
        Returns an error message string if an exception occurs.
    """
    try:
        llm = Ollama(model=model_name)
        response = llm.invoke(prompt_str)
        return response
    except Exception as e:
        error_message = f"Error interacting with Ollama model '{model_name}': {e}. "                         f"Please ensure Ollama is running and the model '{model_name}' is pulled. "                         f"You can pull a model using 'ollama pull {model_name}'."
        print(error_message)
        return error_message # Or raise an exception to be handled by the caller

# Example usage (optional, for testing within this file)
# This requires Ollama to be running and the model (e.g., llama2) to be pulled.
if __name__ == '__main__':
    # Test with a simple prompt
    test_prompt = "Why is the sky blue?"
    print(f"Testing LLM with prompt: '{test_prompt}' using model '{DEFAULT_MODEL}'")
    
    # Make sure Ollama is running and 'llama2' (or DEFAULT_MODEL) is pulled before running this test.
    # e.g., run 'ollama serve' in one terminal, and 'ollama pull llama2' if not already done.
    response = get_llm_response(test_prompt)
    
    print(f"LLM Response:\n{response}")

    # Test with a non-existent model to see error handling
    # print("\nTesting with a non-existent model...")
    # error_response = get_llm_response(test_prompt, model_name="non_existent_model_test")
    # print(f"LLM Error Response:\n{error_response}")
