"""Configuration for BookFinder."""

import os

# Mirror list - ordered by reliability (updated March 2026)
# Note: .li, .se, .org domains were seized/suspended due to legal action
MIRRORS = [
    "https://annas-archive.gd",
    "https://annas-archive.gl",
    "https://annas-archive.pk",
]

# Anna's Archive membership key (optional - set env var for fast downloads)
# Get one by donating at annas-archive.gd/faq#api
AA_KEY = os.environ.get("ANNAS_KEY", "")

# Research library location
LIBRARY_DIR = os.environ.get(
    "BOOKFINDER_LIBRARY",
    os.path.join(os.path.expanduser("~"), "Research", "BookFinder"),
)

# Legacy download directory (kept for web UI compatibility)
DOWNLOAD_DIR = LIBRARY_DIR

# Request settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# Browser settings
BROWSER_TIMEOUT = 60000  # ms to wait for page loads / challenge solving

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Content type options
CONTENT_TYPES = {
    "": "All",
    "book_nonfiction": "Non-fiction",
    "book_fiction": "Fiction",
    "book_unknown": "Unknown",
    "book_comic": "Comics",
    "magazine": "Magazines",
    "standards_document": "Standards",
}

# File extension filters
FILE_EXTENSIONS = {
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
