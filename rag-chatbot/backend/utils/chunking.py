"""
Utility function for splitting text into manageable chunks.

Supports different strategies for plain text and Markdown content
to optimize for semantic coherence where possible.
"""
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
        A list of text chunks. Returns an empty list if the input text is empty.
    """
    if not text:
        return []

    if is_markdown:
        # MarkdownTextSplitter attempts to preserve Markdown structure (headers, lists, etc.)
        # It uses chunk_size as a guideline but may create larger chunks to keep semantic blocks intact.
        # Overlap is not as directly configurable as with RecursiveCharacterTextSplitter.
        # For very large sections without Markdown structural breaks, chunks might exceed chunk_size.
        md_splitter = MarkdownTextSplitter(chunk_size=chunk_size) 
        chunks = md_splitter.split_text(text)
    else:
        # RecursiveCharacterTextSplitter is a general-purpose splitter that tries to split
        # on a list of separators in order until chunks are small enough.
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            # More comprehensive list of separators, ordered by preference for splitting:
            # double newlines (paragraphs), newlines, carriage returns, common sentence endings, spaces.
            separators=["\n\n", "\n", "\r\n", "\r", ". ", "! ", "? ", " ", ""],
            add_start_index=False, # Set to True if byte offsets of chunks are needed
        )
        chunks = recursive_splitter.split_text(text)
    
    # Optional post-processing for Markdown:
    # If MarkdownTextSplitter produces chunks significantly larger than chunk_size,
    # one could iterate through them and re-split oversized ones using RecursiveCharacterTextSplitter.
    # For this project, we accept the output of MarkdownTextSplitter directly.

    return chunks

# Example usage (optional, for local testing)
if __name__ == '__main__':
    sample_text = "This is a long sample text.\n\nIt has paragraphs.\nAnd multiple lines.\n" * 50
    print("--- Recursive Splitting (Plain Text) ---")
    recursive_chunks = chunk_text(sample_text, chunk_size=100, chunk_overlap=20)
    for i, chunk in enumerate(recursive_chunks):
        print(f"Recursive Chunk {i+1} (length {len(chunk)}):\n'{chunk}'\n---")

    markdown_sample = """
# Header 1
This is text under header 1. It's quite long to see if it might be split if chunk_size is small. Let's add more content here. And more. And more.

## Header 2
- List item 1: Some text for this item.
- List item 2: More text to make this list item longer.

This is more text under Header 2.
""" * 5 # Make it longer to test chunking
    print("\n--- Markdown Splitting ---")
    markdown_chunks = chunk_text(markdown_sample, chunk_size=150, chunk_overlap=20, is_markdown=True)
    for i, chunk in enumerate(markdown_chunks):
        print(f"Markdown Chunk {i+1} (length {len(chunk)}):\n'{chunk}'\n---")
    
    long_md_section = "# Title for a Very Long Section\n" + "This is a single, very long line of text without many internal markdown structural elements. " * 100 # Approx 7k chars
    print("\n--- Long Markdown Section Splitting (chunk_size=1000) ---")
    long_md_chunks = chunk_text(long_md_section, chunk_size=1000, is_markdown=True)
    for i, chunk in enumerate(long_md_chunks):
        print(f"Long MD Chunk {i+1} (length {len(chunk)}):\n'{chunk[:200]}...' (first 200 chars)\n---") # Print only snippet
    
    empty_text = ""
    print("\n--- Empty Text Splitting ---")
    empty_chunks = chunk_text(empty_text)
    print(f"Empty text chunks: {empty_chunks}")

    short_text = "This is a short text, shorter than default chunk_size."
    print("\n--- Short Text Splitting (Recursive) ---")
    short_chunks_recursive = chunk_text(short_text) # Use default chunk_size
    for i, chunk in enumerate(short_chunks_recursive):
        print(f"Short Recursive Chunk {i+1} (length {len(chunk)}):\n'{chunk}'\n---")

    print("\n--- Short Text Splitting (Markdown) ---")
    short_chunks_md = chunk_text(short_text, is_markdown=True) # Use default chunk_size
    for i, chunk in enumerate(short_chunks_md):
        print(f"Short Markdown Chunk {i+1} (length {len(chunk)}):\n'{chunk}'\n---")
