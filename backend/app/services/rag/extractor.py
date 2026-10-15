import os
import re
from typing import Tuple
from pypdf import PdfReader
from app.core.logging import logger

def clean_and_normalize_text(raw_text: str) -> str:
    """
    Cleans raw text, normalizes whitespace, and sanitizes dangerous prompt injection markers.
    """
    if not raw_text:
        return ""
    # Normalize unicode and whitespace
    text = re.sub(r'\r\n', '\n', raw_text)
    text = re.sub(r'[\t ]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Prompt injection neutralization in ingested documents
    injection_patterns = [
        re.compile(r'ignore\s+all\s+previous\s+instructions', re.IGNORECASE),
        re.compile(r'system\s+prompt\s*:', re.IGNORECASE),
        re.compile(r'you\s+are\s+now\s+in\s+god\s+mode', re.IGNORECASE),
        re.compile(r'bypass\s+all\s+safety\s+checks', re.IGNORECASE),
    ]
    for pattern in injection_patterns:
        text = pattern.sub('[SANITIZED_INSTRUCTION]', text)

    return text.strip()

def extract_text_from_file(file_path: str) -> Tuple[str, int]:
    """
    Extracts text from PDF, MD, TXT, or JSON files.
    Returns: (normalized_text, page_or_section_count)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    count = 1

    try:
        if ext == ".pdf":
            reader = PdfReader(file_path)
            pages = []
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text() or ""
                if extracted.strip():
                    pages.append(f"--- Page {i+1} ---\n{extracted}")
            text = "\n\n".join(pages)
            count = len(reader.pages)
        elif ext in [".md", ".txt", ".json", ".log", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()

        normalized = clean_and_normalize_text(text)
        return normalized, count
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        raise
