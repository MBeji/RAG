import PyPDF2
import docx
import markdown
from bs4 import BeautifulSoup
import pandas as pd
import os

def extract_text_from_pdf(file_path: str) -> str:
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                extracted_text = page.extract_text()
                if extracted_text: # Ensure text was extracted
                    text += extracted_text
        return text
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading TXT {file_path}: {e}")
        return ""

def extract_text_from_md(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            md_content = file.read()
        html = markdown.markdown(md_content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading MD {file_path}: {e}")
        return ""

def extract_text_from_csv(file_path: str) -> str:
    try:
        df = pd.read_csv(file_path)
        # Simple concatenation of all cells, including headers, then by column
        text_parts = []
        # Add headers
        text_parts.append(",".join(df.columns))
        # Add cell values column by column
        for col in df.columns:
            for item in df[col].astype(str): # Convert all to string
                text_parts.append(item)
        return "\n".join(text_parts)
        # Alternative from example (concatenates rows as strings)
        # return "\n".join(df.apply(lambda row: ', '.join(row.astype(str)), axis=1))
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading CSV {file_path}: {e}")
        return ""

# Example usage (optional, for testing)
if __name__ == '__main__':
    # Create dummy files for testing if needed
    # print(extract_text_from_pdf("path_to.pdf"))
    # print(extract_text_from_docx("path_to.docx"))
    pass
