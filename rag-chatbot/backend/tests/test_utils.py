import pytest
import os
from pathlib import Path

# This assumes pytest is run from the 'rag-chatbot/backend/' directory.
# If run from project root, imports might need to be 'backend.utils.parser' etc.
# For consistency with how the app runs, we'll assume utils is directly importable
# as if 'backend' is the current working directory or in PYTHONPATH.
from utils.parser import (
    extract_text_from_txt,
    # extract_text_from_md # Can add if more complex MD testing is needed
)
from utils.chunking import chunk_text

@pytest.fixture
def temp_file_dir(tmp_path: Path) -> Path:
    # tmp_path is a pytest fixture providing a temporary directory unique to the test run
    test_files_dir = tmp_path / "test_files_sub_dir" # Using a sub-directory within tmp_path
    test_files_dir.mkdir()
    return test_files_dir

def test_extract_text_from_txt_simple(temp_file_dir: Path):
    file_path = temp_file_dir / "test.txt"
    expected_content = "This is a simple test file.\nWith multiple lines."
    file_path.write_text(expected_content, encoding='utf-8') # Specify encoding
    
    assert extract_text_from_txt(str(file_path)) == expected_content

def test_extract_text_from_txt_non_existent():
    # Parser functions are designed to print an error and return ""
    # We can't easily assert the print, but can check the return value.
    assert extract_text_from_txt("non_existent_file_for_sure.txt") == ""

def test_chunk_text_empty():
    assert chunk_text("") == []

def test_chunk_text_short_text_no_chunking():
    text = "This is a short text, shorter than chunk_size."
    # Using default chunk_size=1000, overlap=200
    chunks = chunk_text(text) 
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunk_text_long_text_recursive_splitting():
    # Text length is 53 * 10 = 530 characters.
    text = "This is a very long string that needs to be chunked. " * 10 
    # Default chunk_size=1000, so it should be 1 chunk.
    chunks_default_size = chunk_text(text)
    assert len(chunks_default_size) == 1
    assert chunks_default_size[0] == text

    # Now test with a smaller chunk_size to force splitting
    chunks_small_size = chunk_text(text, chunk_size=100, chunk_overlap=10)
    assert len(chunks_small_size) > 1 # Should be multiple chunks

    # Basic overlap check for recursive splitter
    if len(chunks_small_size) > 1:
        overlap_len = 10 
        # A simple check: the end of the first chunk should have some overlap with the start of the second.
        # This is not perfectly precise due to splitting on separators but gives an indication.
        # Example: chunk0_end = "chunked. ", chunk1_start = "unked. This"
        # We check if a part of the end of chunk0 is in the beginning of chunk1
        # This is a heuristic and might need refinement based on actual splitter behavior.
        # A better test might be to construct text where overlap is very predictable.
        end_of_first = chunks_small_size[0][-(overlap_len + 15):] # Get a slightly larger slice from end
        start_of_second = chunks_small_size[1][:(overlap_len + 15)] # Get a slightly larger slice from start
        
        # Find common substring - this is tricky because exact overlap depends on separators
        # For a simple test, let's check if the last word of chunk0 (or part of it) is in start of chunk1
        first_chunk_words = chunks_small_size[0].split()
        if first_chunk_words:
            last_word_first_chunk = first_chunk_words[-1]
            assert last_word_first_chunk in start_of_second


def test_chunk_text_markdown_basic():
    md_text = "# Title\nThis is some markdown text.\n## Subtitle\n- Point 1\n- Point 2"
    # MarkdownTextSplitter uses chunk_size as a guide but prioritizes semantic structure.
    # With default chunk_size=1000, this short text should remain one chunk.
    chunks = chunk_text(md_text, chunk_size=1000, is_markdown=True)
    assert len(chunks) == 1 
    assert "Title" in chunks[0]
    assert "Point 2" in chunks[0]

def test_chunk_text_markdown_splitting_by_headers():
    # MarkdownTextSplitter tries to split by headers first if content is too long.
    # Each "Section X" part is ~230 chars (20 * (5+1+5+1) + len("# Section X\n"))
    # If chunk_size is e.g. 150, it should split by headers.
    md_text_long = ("# Section 1\n" + "abcde fghij " * 20 + "\n" + # Approx 230 chars
                    "# Section 2\n" + "klmno pqrst " * 20 + "\n" + # Approx 230 chars
                    "# Section 3\n" + "uvwxyz abcde " * 20)       # Approx 230 chars
    
    chunks_md = chunk_text(md_text_long, chunk_size=150, is_markdown=True) # chunk_size is smaller than sections
    
    assert len(chunks_md) >= 3 # Expecting it to split by headers
    if len(chunks_md) >= 3:
        assert "# Section 1" in chunks_md[0]
        assert "pqrst" not in chunks_md[0] # Content from section 2 shouldn't be in chunk 0
        assert "# Section 2" in chunks_md[1]
        assert "abcde fghij" not in chunks_md[1] # Content from section 1 shouldn't be in chunk 1
        assert "# Section 3" in chunks_md[2]
    
    # Test with chunk_size large enough to hold one section but not two
    chunks_md_larger_size = chunk_text(md_text_long, chunk_size=250, is_markdown=True)
    assert len(chunks_md_larger_size) >= 3 # Still expects splits by header due to MarkdownTextSplitter behavior
    if len(chunks_md_larger_size) >=3:
         assert "# Section 1" in chunks_md_larger_size[0]
         assert "# Section 2" in chunks_md_larger_size[1]
         assert "# Section 3" in chunks_md_larger_size[2]


def test_chunk_text_markdown_very_long_section_no_header_split():
    # Test behavior when a single markdown section (e.g., paragraph under a header)
    # is longer than chunk_size. MarkdownTextSplitter might still keep it as one chunk
    # if there are no further sub-headers or markdown structural elements to split by.
    # The current MarkdownTextSplitter might not perfectly enforce chunk_size within large text blocks
    # without further markdown structure.
    long_paragraph = "This is a single very long paragraph without much internal markdown structure. " * 50 # ~2800 chars
    md_text = f"# Only Header\n{long_paragraph}"
    
    chunks = chunk_text(md_text, chunk_size=1000, is_markdown=True)
    assert len(chunks) >= 1 # Might be 1 or more depending on how it handles overflow
    assert "# Only Header" in chunks[0]
    
    # For such cases, if strict chunk_size is needed post-MarkdownTextSplitter,
    # one might need to re-chunk oversized chunks with RecursiveCharacterTextSplitter.
    # This test just verifies current behavior.
    # If it does split, ensure the header is likely in the first chunk.
    if len(chunks) > 1:
        # This is an assumption that might not hold for all versions or configurations.
        # The main point is that MarkdownTextSplitter prioritizes structure.
        print(f"Warning: Long MD section split into {len(chunks)} chunks. First chunk len: {len(chunks[0])}")

# Note for running tests:
# 1. Navigate to the `rag-chatbot/backend/` directory.
# 2. Activate your Python virtual environment (e.g., `source .venv/bin/activate`).
# 3. Run pytest: `pytest` or `python -m pytest`.
# Ensure that Ollama is NOT required for these unit tests, as they focus on utilities.
# If any utility inadvertently tries to connect to services, tests might fail or hang.
# The current parser and chunking utils don't seem to require external services.
```
