from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Splits the given text into chunks using RecursiveCharacterTextSplitter.

    Args:
        text: The text to split.
        chunk_size: The maximum size of each chunk (in characters).
        chunk_overlap: The overlap between consecutive chunks (in characters).

    Returns:
        A list of text chunks.
    """
    if not text:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

# Example usage (optional, for testing)
if __name__ == '__main__':
    sample_text = "This is a long sample text to test the chunking functionality. " * 100
    chunks = chunk_text(sample_text)
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1} (length {len(chunk)}):\n{chunk}\n---")
    
    short_text = "This is a short text."
    chunks_short = chunk_text(short_text)
    print(f"Short text chunks: {chunks_short}")
    
    empty_text = ""
    chunks_empty = chunk_text(empty_text)
    print(f"Empty text chunks: {chunks_empty}")
