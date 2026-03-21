"""PDF/EPUB to Markdown extraction for BookFinder."""

import os
import re


def extract_to_markdown(filepath: str) -> str:
    """
    Extract text content from a PDF or EPUB file and return as markdown.

    Uses pymupdf4llm for high-quality extraction that preserves:
    - Headings and structure
    - Tables
    - Lists
    - Image references
    - Page breaks
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return _extract_pdf(filepath)
    elif ext == ".epub":
        return _extract_epub(filepath)
    elif ext == ".djvu":
        return _extract_djvu(filepath)
    elif ext in (".mobi", ".azw3", ".fb2"):
        return _extract_ebook(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _extract_pdf(filepath: str) -> str:
    """Extract markdown from PDF using pymupdf4llm."""
    import pymupdf4llm

    md_text = pymupdf4llm.to_markdown(filepath)
    return _clean_markdown(md_text)


def _extract_epub(filepath: str) -> str:
    """Extract text from EPUB files."""
    import zipfile
    from bs4 import BeautifulSoup

    text_parts = []

    with zipfile.ZipFile(filepath, "r") as zf:
        for name in zf.namelist():
            if name.endswith((".xhtml", ".html", ".htm")):
                with zf.open(name) as f:
                    soup = BeautifulSoup(f.read(), "lxml")

                    # Remove scripts and styles
                    for tag in soup(["script", "style"]):
                        tag.decompose()

                    # Convert headings
                    for i in range(1, 7):
                        for h in soup.find_all(f"h{i}"):
                            h.string = f"{'#' * i} {h.get_text(strip=True)}"

                    text = soup.get_text(separator="\n")
                    if text.strip():
                        text_parts.append(text.strip())

    return _clean_markdown("\n\n".join(text_parts))


def _extract_djvu(filepath: str) -> str:
    """Extract text from DJVU files using pymupdf."""
    import pymupdf

    doc = pymupdf.open(filepath)
    text_parts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_parts.append(f"<!-- Page {page_num + 1} -->\n\n{text.strip()}")

    doc.close()
    return _clean_markdown("\n\n---\n\n".join(text_parts))


def _extract_ebook(filepath: str) -> str:
    """Fallback extraction for other ebook formats using pymupdf."""
    import pymupdf

    try:
        doc = pymupdf.open(filepath)
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(text.strip())

        doc.close()
        return _clean_markdown("\n\n".join(text_parts))
    except Exception as e:
        raise ValueError(f"Could not extract text from {filepath}: {e}")


def _clean_markdown(text: str) -> str:
    """Clean up extracted markdown text."""
    # Remove excessive blank lines
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    # Remove trailing whitespace on lines
    text = re.sub(r"[ \t]+\n", "\n", text)
    # Fix broken words from line wrapping (common in PDFs)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    return text.strip()
