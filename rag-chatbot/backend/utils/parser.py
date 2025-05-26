"""
Utility functions for extracting text content from various file formats.

Each function is designed to handle potential errors like FileNotFoundError
or issues during parsing, returning an empty string in such cases.
The calling code should check for empty string results to determine if extraction failed.
"""
import PyPDF2
import docx
import markdown
from bs4 import BeautifulSoup
import pandas as pd
# import os # Removed as os module was not used

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text content from a PDF file.

    Args:
        file_path: The path to the PDF file.

    Returns:
        A string containing the extracted text, or an empty string if
        the file is not found or an error occurs during parsing.
    """
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text_parts = [] # Use a list for potentially better performance with many pages
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                extracted_text = page.extract_text()
                if extracted_text:
                    text_parts.append(extracted_text)
            return "".join(text_parts)
    except FileNotFoundError:
        print(f"Error: PDF file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """
    Extracts all text content from a DOCX file.
    Each paragraph's text is followed by a newline character.

    Args:
        file_path: The path to the DOCX file.

    Returns:
        A string containing the extracted text, or an empty string if
        the file is not found or an error occurs during parsing.
    """
    try:
        doc = docx.Document(file_path)
        text_parts = []
        for para in doc.paragraphs:
            text_parts.append(para.text)
        return "\n".join(text_parts)
    except FileNotFoundError:
        print(f"Error: DOCX file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """
    Extracts all text content from a plain text file (UTF-8 encoded).

    Args:
        file_path: The path to the TXT file.

    Returns:
        A string containing the file's content, or an empty string if
        the file is not found or an error occurs during reading.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: TXT file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading TXT {file_path}: {e}")
        return ""

def extract_text_from_md(file_path: str) -> str:
    """
    Extracts text content from a Markdown file.
    Converts Markdown to HTML, then extracts text from HTML.

    Args:
        file_path: The path to the MD file.

    Returns:
        A string containing the extracted text, or an empty string if
        the file is not found or an error occurs during parsing.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            md_content = file.read()
        html = markdown.markdown(md_content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    except FileNotFoundError:
        print(f"Error: MD file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading MD {file_path}: {e}")
        return ""

def extract_text_from_csv(file_path: str) -> str:
    """
    Extracts text content from a CSV file.
    The current implementation concatenates headers and then all cell values,
    column by column, separated by newlines.

    Args:
        file_path: The path to the CSV file.

    Returns:
        A string representation of the CSV content, or an empty string if
        the file is not found or an error occurs during parsing.
    """
    try:
        df = pd.read_csv(file_path)
        # Concatenates headers, then all cell values column by column, separated by newlines.
        # This provides a simple textual representation.
        text_parts = []
        # Add headers as a comma-separated string
        text_parts.append(",".join(df.columns))
        # Add cell values, iterating column by column
        for col in df.columns:
            for item in df[col].astype(str): # Convert all items to string
                text_parts.append(item)
        return "\n".join(text_parts)
        # Alternative (from original example - concatenates rows as strings):
        # return "\n".join(df.apply(lambda row: ', '.join(row.astype(str)), axis=1))
    except FileNotFoundError:
        print(f"Error: CSV file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading CSV {file_path}: {e}")
        return ""

# Example usage (optional, for local testing)
if __name__ == '__main__':
    # To test, create dummy files or provide paths to existing ones.
    # For example:
    # Create a dummy_test.txt file in the same directory as parser.py
    # with open("dummy_test.txt", "w") as f:
    #     f.write("Hello from dummy_test.txt!")
    # print(f"TXT Test: '{extract_text_from_txt('dummy_test.txt')}'")

    # Create a dummy_test.md
    # with open("dummy_test.md", "w") as f:
    #     f.write("# Markdown Test\nThis is **bold**.")
    # print(f"MD Test: '{extract_text_from_md('dummy_test.md')}'")
    pass
