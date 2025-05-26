from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownTextSplitter

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200, is_markdown: bool = False) -> list[str]:
    """
    Splits the given text into chunks.
    Uses MarkdownTextSplitter if is_markdown is True, otherwise RecursiveCharacterTextSplitter.

    Args:
        text: The text to split.
        chunk_size: The maximum size of each chunk (in characters).
        chunk_overlap: The overlap between consecutive chunks (in characters).
        is_markdown: Flag to indicate if the text is Markdown.

    Returns:
        A list of text chunks.
    """
    if not text:
        return []

    if is_markdown:
        # MarkdownTextSplitter is good for structure but might produce larger chunks than chunk_size
        # if a section is very large. It tries to keep semantic blocks together.
        # It doesn't use chunk_overlap in the same way as RecursiveCharacterTextSplitter.
        # You might need to further process chunks from MarkdownTextSplitter if they are too large.
        md_splitter = MarkdownTextSplitter(chunk_size=chunk_size) # Overlap not directly supported in the same way
        chunks = md_splitter.split_text(text)
    else:
        # For general text, RecursiveCharacterTextSplitter with better separators
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "\r\n", "\r", ". ", "! ", "? ", " ", ""], # More comprehensive separators
            add_start_index=False, # Can be useful for some applications but not essential here
        )
        chunks = recursive_splitter.split_text(text)
    
    # Post-processing for Markdown chunks that might be too large (optional refinement)
    # For now, we'll accept what MarkdownTextSplitter gives.
    # A more robust solution might re-split oversized markdown chunks using RecursiveCharacterTextSplitter.

    return chunks

# Example usage (optional, for testing)
if __name__ == '__main__':
    sample_text = "This is a long sample text.\n\nIt has paragraphs.\nAnd multiple lines.\n" * 50
    print("--- Recursive Splitting ---")
    recursive_chunks = chunk_text(sample_text, chunk_size=100, chunk_overlap=20)
    for i, chunk in enumerate(recursive_chunks):
        print(f"Recursive Chunk {i+1} (length {len(chunk)}):\n'{chunk}'\n---")

    markdown_sample = """
# Header 1
This is text under header 1.

## Header 2
- List item 1
- List item 2

This is more text.
""" * 10 # Make it longer to test chunking
    print("\n--- Markdown Splitting ---")
    markdown_chunks = chunk_text(markdown_sample, chunk_size=100, chunk_overlap=20, is_markdown=True)
    for i, chunk in enumerate(markdown_chunks):
        print(f"Markdown Chunk {i+1} (length {len(chunk)}):\n'{chunk}'\n---")
    
    # Test how MarkdownTextSplitter handles chunk_size for very long sections without natural breaks
    long_md_section = "# Title\n" + "a b c " * 200 # Approx 800 chars + title
    print("\n--- Long Markdown Section Splitting ---")
    long_md_chunks = chunk_text(long_md_section, chunk_size=200, is_markdown=True)
    for i, chunk in enumerate(long_md_chunks):
        print(f"Long MD Chunk {i+1} (length {len(chunk)}):\n'{chunk}'\n---")
    
    empty_text = ""
    print("\n--- Empty Text Splitting ---")
    empty_chunks = chunk_text(empty_text)
    print(f"Empty text chunks: {empty_chunks}")

    short_text = "This is a short text, shorter than chunk_size."
    print("\n--- Short Text Splitting (Recursive) ---")
    short_chunks_recursive = chunk_text(short_text, chunk_size=100, chunk_overlap=20)
    for i, chunk in enumerate(short_chunks_recursive):
        print(f"Short Recursive Chunk {i+1} (length {len(chunk)}):\n'{chunk}'\n---")

    print("\n--- Short Text Splitting (Markdown) ---")
    short_chunks_md = chunk_text(short_text, chunk_size=100, is_markdown=True) # is_markdown is true
    for i, chunk in enumerate(short_chunks_md):
        print(f"Short Markdown Chunk {i+1} (length {len(chunk)}):\n'{chunk}'\n---")
