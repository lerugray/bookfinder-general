"""Configuration for BookFinder."""

from __future__ import annotations

import os
from typing import Final

# Mirror list - ordered by reliability (updated March 2026)
# Note: .li, .se, .org domains were seized/suspended due to legal action
MIRRORS: Final[list[str]] = [
    "https://annas-archive.gd",
    "https://annas-archive.gl",
    "https://annas-archive.pk",
]

# Anna's Archive membership key (optional - set env var for fast downloads)
# Get one by donating at annas-archive.gd/faq#api
AA_KEY: Final[str] = os.environ.get("ANNAS_KEY", "")

# Research library location
LIBRARY_DIR: Final[str] = os.environ.get(
    "BOOKFINDER_LIBRARY",
    os.path.join(os.path.expanduser("~"), "Research", "BookFinder"),
)

# Legacy download directory (kept for web UI compatibility)
DOWNLOAD_DIR: Final[str] = LIBRARY_DIR

# Auto-sync library to git after downloads (opt-in)
LIBRARY_SYNC: Final[bool] = os.environ.get("BOOKFINDER_SYNC", "").lower() in ("true", "1", "yes")

# Request settings
REQUEST_TIMEOUT: Final[int] = 30
MAX_RETRIES: Final[int] = 3

# Browser settings
BROWSER_TIMEOUT: Final[int] = 60000  # ms to wait for page loads / challenge solving

HEADERS: Final[dict[str, str]] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Content type options
CONTENT_TYPES: Final[dict[str, str]] = {
    "": "All",
    "book_nonfiction": "Non-fiction",
    "book_fiction": "Fiction",
    "book_unknown": "Unknown",
    "book_comic": "Comics",
    "magazine": "Magazines",
    "standards_document": "Standards",
}

# File extension filters
FILE_EXTENSIONS: Final[dict[str, str]] = {
    "": "All",
    "pdf": "PDF",
    "epub": "EPUB",
    "mobi": "MOBI",
    "djvu": "DJVU",
    "azw3": "AZW3",
    "fb2": "FB2",
    "cbr": "CBR",
    "cbz": "CBZ",
}
