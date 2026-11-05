import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Tuple, Optional

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file using available libraries:
    1. PyMuPDF (fitz)
    2. pdfplumber
    3. pypdf
    4. Fallback pure Python text stream extraction
    """
    # 1. Try PyMuPDF
    try:
        import fitz
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            t = page.get_text()
            if t:
                text_parts.append(t)
        doc.close()
        text = "\n".join(text_parts).strip()
        if text:
            return text
    except Exception:
        pass

    # 2. Try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text_parts = [page.extract_text() for page in pdf.pages if page.extract_text()]
            text = "\n".join(text_parts).strip()
            if text:
                return text
    except Exception:
        pass

    # 3. Try pypdf / PyPDF2
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text_parts = [page.extract_text() for page in reader.pages if page.extract_text()]
        text = "\n".join(text_parts).strip()
        if text:
            return text
    except Exception:
        pass

    # 4. Pure Python PDF Fallback (Extract literal text streams via regex)
    try:
        with open(file_path, "rb") as f:
            content = f.read().decode("latin1", errors="ignore")
        # Extract content between BT (Begin Text) and ET (End Text)
        text_blocks = []
        # Match TJ or Tj operations
        tj_matches = re.findall(r'\((.*?)\)\s*Tj', content)
        if tj_matches:
            text_blocks.extend(tj_matches)
        
        # Match array Tj format e.g. [(Hello) -20 (World)] TJ
        array_matches = re.findall(r'\[(.*?)\]\s*TJ', content)
        for arr in array_matches:
            parts = re.findall(r'\((.*?)\)', arr)
            if parts:
                text_blocks.append("".join(parts))

        if text_blocks:
            return "\n".join(text_blocks).strip()
    except Exception:
        pass

    return ""


def extract_text_from_docx(file_path: str) -> str:
    """
    Extracts text from a DOCX file using python-docx with pure Python zipfile fallback.
    """
    # 1. Try python-docx
    try:
        import docx
        doc = docx.Document(file_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text_parts.append(paragraph.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_parts.append(" | ".join(row_text))
        text = "\n".join(text_parts).strip()
        if text:
            return text
    except Exception:
        pass

    # 2. Pure Python standard library fallback using zipfile & XML
    try:
        with zipfile.ZipFile(file_path, 'r') as docx_zip:
            xml_content = docx_zip.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            # Find all text elements <w:t>
            namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs = []
            for p in tree.findall('.//w:p', namespace):
                texts = [node.text for node in p.findall('.//w:t', namespace) if node.text]
                if texts:
                    paragraphs.append("".join(texts))
            if paragraphs:
                return "\n".join(paragraphs).strip()
    except Exception:
        pass

    return ""


def extract_text_from_file(file_path: str) -> Tuple[str, str]:
    """
    Identifies the file type and extracts raw text.
    Returns (raw_text, detected_type).
    """
    ext = os.path.splitext(file_path)[1].lower()
    raw_text = ""
    
    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
        file_type = "PDF"
    elif ext in [".docx", ".doc"]:
        raw_text = extract_text_from_docx(file_path)
        file_type = "DOCX"
    elif ext in [".txt", ".rtf", ".csv"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read()
        except Exception:
            with open(file_path, "r", encoding="latin1", errors="ignore") as f:
                raw_text = f.read()
        file_type = "TXT"
    else:
        file_type = ext.replace(".", "").upper()

    return raw_text.strip(), file_type
