"""Research library management for BookFinder.

Manages downloaded books in a structured library with metadata,
extracted text, and translations.
"""

import json
import os
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .config import LIBRARY_DIR


@dataclass
class BookEntry:
    """A book in the research library."""
    id: str
    title: str
    author: str
    year: str
    language: str
    extension: str
    filesize: str
    md5: str
    source_url: str
    downloaded_at: str
    original_file: str
    has_content: bool = False
    has_translation: bool = False
    tags: list[str] = field(default_factory=list)

    @property
    def dir_path(self) -> str:
        return os.path.join(LIBRARY_DIR, self.id)

    @property
    def content_path(self) -> str:
        return os.path.join(self.dir_path, "content.md")

    @property
    def translated_path(self) -> str:
        return os.path.join(self.dir_path, "content_en.md")

    @property
    def metadata_path(self) -> str:
        return os.path.join(self.dir_path, "metadata.json")


def _slugify(text: str) -> str:
    """Create a filesystem-safe slug from text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-")


def ensure_library() -> str:
    """Create library directory if needed."""
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    return LIBRARY_DIR


def generate_book_id(title: str, author: str, md5: str) -> str:
    """Generate a unique, readable directory name for a book."""
    slug = _slugify(title)
    if author:
        author_slug = _slugify(author.split(",")[0].split(" ")[-1])  # Last name
        slug = f"{slug}-{author_slug}"
    # Add short md5 suffix for uniqueness
    slug = f"{slug}-{md5[:8]}"
    return slug


def save_book(
    filepath: str,
    title: str,
    author: str,
    year: str,
    language: str,
    extension: str,
    filesize: str,
    md5: str,
    source_url: str,
    extract_text: bool = True,
    translate: bool = True,
    project_dir: str | None = None,
) -> BookEntry:
    """
    Save a downloaded book to the research library.

    Creates the library entry with:
    - Original file
    - Extracted markdown content
    - English translation (if non-English and translate=True)
    - Metadata JSON

    Args:
        filepath: Path to the downloaded file.
        title: Book title.
        author: Book author.
        year: Publication year.
        language: Book language.
        extension: File extension.
        filesize: File size string.
        md5: MD5 hash from Anna's Archive.
        source_url: URL the book was downloaded from.
        extract_text: Whether to extract text to markdown.
        translate: Whether to translate non-English books.
        project_dir: If set, also copy the book to this project directory.

    Returns:
        BookEntry with all paths populated.
    """
    ensure_library()

    book_id = generate_book_id(title, author, md5)
    book_dir = os.path.join(LIBRARY_DIR, book_id)
    os.makedirs(book_dir, exist_ok=True)

    # Copy original file
    original_filename = f"original.{extension}" if extension else os.path.basename(filepath)
    original_dest = os.path.join(book_dir, original_filename)
    if not os.path.exists(original_dest):
        shutil.copy2(filepath, original_dest)

    entry = BookEntry(
        id=book_id,
        title=title,
        author=author,
        year=year,
        language=language,
        extension=extension,
        filesize=filesize,
        md5=md5,
        source_url=source_url,
        downloaded_at=datetime.now().isoformat(),
        original_file=original_filename,
    )

    # Extract text to markdown
    if extract_text:
        try:
            from .extractor import extract_to_markdown
            content = extract_to_markdown(original_dest)
            if content:
                # Add header with metadata
                header = f"# {title}\n\n"
                if author:
                    header += f"**Author:** {author}\n"
                if year:
                    header += f"**Year:** {year}\n"
                if language:
                    header += f"**Language:** {language}\n"
                header += f"\n---\n\n"

                with open(entry.content_path, "w", encoding="utf-8") as f:
                    f.write(header + content)
                entry.has_content = True
        except Exception as e:
            # Log but don't fail — the original file is still saved
            print(f"Warning: Text extraction failed: {e}")

    # Translate if non-English
    if translate and entry.has_content and language and language.lower() not in ("english", "en"):
        try:
            from .translator import translate_text, detect_language

            with open(entry.content_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Detect language code for translator
            lang_map = {
                "german": "de", "french": "fr", "spanish": "es",
                "italian": "it", "portuguese": "pt", "russian": "ru",
                "dutch": "nl", "polish": "pl", "swedish": "sv",
                "czech": "cs", "latin": "la", "chinese": "zh-CN",
                "japanese": "ja",
            }
            source_lang = lang_map.get(language.lower(), "auto")

            translated = translate_text(content, source_lang=source_lang, target_lang="en")
            if translated:
                with open(entry.translated_path, "w", encoding="utf-8") as f:
                    f.write(translated)
                entry.has_translation = True
        except Exception as e:
            print(f"Warning: Translation failed: {e}")

    # Save metadata
    _save_metadata(entry)

    # Copy to project directory if requested
    if project_dir:
        _copy_to_project(entry, project_dir)

    return entry


def _save_metadata(entry: BookEntry):
    """Save book metadata to JSON."""
    data = asdict(entry)
    with open(entry.metadata_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _copy_to_project(entry: BookEntry, project_dir: str):
    """Copy book files to a project's research directory."""
    dest_dir = os.path.join(project_dir, "research", entry.id)
    os.makedirs(dest_dir, exist_ok=True)

    for filename in os.listdir(entry.dir_path):
        src = os.path.join(entry.dir_path, filename)
        dst = os.path.join(dest_dir, filename)
        if os.path.isfile(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)


def list_books(query: str = "") -> list[BookEntry]:
    """
    List all books in the library, optionally filtered by query.

    Query matches against title, author, and tags.
    """
    ensure_library()
    books = []

    for entry_name in sorted(os.listdir(LIBRARY_DIR)):
        metadata_path = os.path.join(LIBRARY_DIR, entry_name, "metadata.json")
        if os.path.isfile(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entry = BookEntry(**{k: v for k, v in data.items() if k in BookEntry.__dataclass_fields__})
                if query:
                    searchable = f"{entry.title} {entry.author} {' '.join(entry.tags)}".lower()
                    if query.lower() not in searchable:
                        continue
                books.append(entry)
            except Exception:
                continue

    return books


def get_book(book_id: str) -> BookEntry | None:
    """Get a specific book by ID."""
    metadata_path = os.path.join(LIBRARY_DIR, book_id, "metadata.json")
    if not os.path.isfile(metadata_path):
        return None

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return BookEntry(**{k: v for k, v in data.items() if k in BookEntry.__dataclass_fields__})
    except Exception:
        return None


def get_book_content(book_id: str, translated: bool = False, max_chars: int = 0) -> str | None:
    """
    Get the text content of a book.

    Args:
        book_id: The book's library ID.
        translated: If True, return English translation (if available).
        max_chars: If > 0, truncate to this many characters.

    Returns:
        The book's markdown content, or None if not found.
    """
    book = get_book(book_id)
    if not book:
        return None

    # Prefer translated version if requested and available
    if translated and book.has_translation:
        path = book.translated_path
    elif book.has_content:
        path = book.content_path
    else:
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if max_chars > 0 and len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... [truncated at {max_chars} characters]"
        return content
    except Exception:
        return None


def search_library(query: str, max_results: int = 10) -> list[dict]:
    """
    Full-text search across all books in the library.

    Returns matching excerpts with context.
    """
    results = []
    query_lower = query.lower()

    for book in list_books():
        # Search in content files
        for content_file in ["content_en.md", "content.md"]:
            filepath = os.path.join(book.dir_path, content_file)
            if not os.path.isfile(filepath):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                if query_lower in content.lower():
                    # Find matching excerpts
                    excerpts = _find_excerpts(content, query, context_chars=200)
                    results.append({
                        "book_id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "file": content_file,
                        "excerpts": excerpts[:3],  # Top 3 matches
                    })
                    break  # Don't search both files for same book
            except Exception:
                continue

        if len(results) >= max_results:
            break

    return results


def _find_excerpts(text: str, query: str, context_chars: int = 200) -> list[str]:
    """Find excerpts containing the query with surrounding context."""
    excerpts = []
    text_lower = text.lower()
    query_lower = query.lower()
    start = 0

    while True:
        idx = text_lower.find(query_lower, start)
        if idx == -1:
            break

        # Get surrounding context
        excerpt_start = max(0, idx - context_chars)
        excerpt_end = min(len(text), idx + len(query) + context_chars)

        excerpt = text[excerpt_start:excerpt_end].strip()
        if excerpt_start > 0:
            excerpt = "..." + excerpt
        if excerpt_end < len(text):
            excerpt = excerpt + "..."

        excerpts.append(excerpt)
        start = idx + len(query)

        if len(excerpts) >= 5:
            break

    return excerpts
