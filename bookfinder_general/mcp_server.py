"""BookFinder MCP Server.

Provides AI assistants with tools to search, download, and read research books.
Connect this server to Claude Code, Cursor, or any MCP-compatible AI tool.
"""

import asyncio
import json
import os
import sys

from mcp.server.fastmcp import FastMCP

from .config import LIBRARY_DIR
from .library import (
    BookEntry,
    get_book,
    get_book_content,
    list_books,
    save_book,
    search_library,
)

mcp = FastMCP(
    "bookfinder-general",
    instructions=(
        "Bookfinder General helps you search for, download, and read research books. "
        "Use search_books to find books on Anna's Archive, download_book to "
        "save them with extracted text and translations, read_book to analyze content, "
        "and summarize_book to create clean research summaries with PDF reports."
    ),
)


@mcp.tool()
async def search_books(
    query: str,
    language: str = "",
    file_format: str = "",
    content_type: str = "",
) -> str:
    """Search Anna's Archive for books.

    Args:
        query: Search terms — works with titles in any language, author names,
               ISBN, or topic descriptions.
        language: Filter by language code (e.g. 'en', 'de', 'fr'). Empty for all.
        file_format: Filter by file type (e.g. 'pdf', 'epub'). Empty for all.
        content_type: Filter by content type ('book_nonfiction', 'book_fiction',
                      'magazine', etc.). Empty for all.

    Returns:
        JSON array of search results with title, author, year, format, size, and md5.
    """
    from .search import search

    def _do_search():
        return search(
            query=query,
            lang=language,
            ext=file_format,
            content=content_type,
        )

    try:
        results, mirror = await asyncio.to_thread(_do_search)
    except ConnectionError as e:
        return json.dumps({"error": str(e)})

    if not results:
        return json.dumps({"results": [], "message": "No results found. Try different search terms."})

    return json.dumps({
        "results": [
            {
                "title": r.title,
                "author": r.author,
                "year": r.year,
                "language": r.language,
                "format": r.extension,
                "size": r.filesize,
                "md5": r.md5,
            }
            for r in results
        ],
        "count": len(results),
        "mirror": mirror,
    }, ensure_ascii=False)


@mcp.tool()
async def download_book(
    md5: str,
    title: str = "",
    author: str = "",
    year: str = "",
    language: str = "",
    save_to_project: bool = False,
    project_path: str = "",
    translate: bool = True,
) -> str:
    """Download a book and process it for research use.

    Downloads the book, extracts text to readable markdown, and translates
    non-English books to English. The processed book is saved to the
    research library.

    Args:
        md5: The MD5 hash of the book (from search_books results).
        title: Book title (for organizing the library).
        author: Book author.
        year: Publication year.
        language: Book language (triggers translation if not English).
        save_to_project: If True, also saves a copy to the current project's
                         research/ folder.
        project_path: Path to the project directory (used with save_to_project).
        translate: Whether to auto-translate non-English books to English.

    Returns:
        JSON with the book's library ID and paths to all generated files.
    """
    from .download import try_download_from_links
    from .search import get_download_links

    # Check if already downloaded
    existing = [b for b in list_books() if b.md5 == md5]
    if existing:
        book = existing[0]
        result = {
            "status": "already_downloaded",
            "book_id": book.id,
            "title": book.title,
            "has_content": book.has_content,
            "has_translation": book.has_translation,
            "library_path": book.dir_path,
        }
        if save_to_project and project_path:
            from .library import _copy_to_project
            _copy_to_project(book, project_path)
            result["project_path"] = os.path.join(project_path, "research", book.id)
        return json.dumps(result)

    # Get download links (runs sync Playwright in a thread)
    def _get_links():
        return get_download_links(md5)

    try:
        links = await asyncio.to_thread(_get_links)
    except ConnectionError as e:
        return json.dumps({"error": f"Could not get download links: {e}"})

    if not links:
        return json.dumps({"error": "No download links found for this book."})

    # Download the file (also uses browser, so run in thread)
    ext = "pdf"  # Default extension
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="bookfinder_")

    def _do_download():
        return try_download_from_links(
            links=links,
            title=title or md5,
            extension=ext,
            download_dir=temp_dir,
        )

    filepath = await asyncio.to_thread(_do_download)

    if not filepath:
        return json.dumps({"error": "Download failed — all mirror sources were unavailable."})

    # Detect actual extension from downloaded file
    actual_ext = os.path.splitext(filepath)[1].lstrip(".").lower()
    if actual_ext:
        ext = actual_ext

    # Save to library with extraction and translation
    def _do_save():
        return save_book(
            filepath=filepath,
            title=title or "Unknown",
            author=author,
            year=year,
            language=language,
            extension=ext,
            filesize="",
            md5=md5,
            source_url=f"annas-archive/md5/{md5}",
            extract_text=True,
            translate=translate and bool(language) and language.lower() not in ("english", "en"),
            project_dir=project_path if save_to_project else None,
        )

    try:
        entry = await asyncio.to_thread(_do_save)
    except Exception as e:
        return json.dumps({"error": f"Failed to process book: {e}"})

    # Clean up temp file
    try:
        os.remove(filepath)
        os.rmdir(temp_dir)
    except Exception:
        pass

    result = {
        "status": "downloaded",
        "book_id": entry.id,
        "title": entry.title,
        "library_path": entry.dir_path,
        "has_content": entry.has_content,
        "has_translation": entry.has_translation,
        "files": {
            "original": entry.original_file,
            "content": "content.md" if entry.has_content else None,
            "translation": "content_en.md" if entry.has_translation else None,
        },
    }
    if save_to_project and project_path:
        result["project_path"] = os.path.join(project_path, "research", entry.id)

    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def list_library(query: str = "") -> str:
    """List books in the research library.

    Args:
        query: Optional search filter — matches against title, author, and tags.
               Leave empty to list all books.

    Returns:
        JSON array of books in the library with metadata.
    """
    books = list_books(query)

    if not books:
        if query:
            return json.dumps({"books": [], "message": f"No books matching '{query}' in library."})
        return json.dumps({"books": [], "message": "Library is empty. Use search_books and download_book to add books."})

    return json.dumps({
        "books": [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "year": b.year,
                "language": b.language,
                "format": b.extension,
                "has_content": b.has_content,
                "has_translation": b.has_translation,
            }
            for b in books
        ],
        "count": len(books),
        "library_path": LIBRARY_DIR,
    }, ensure_ascii=False)


@mcp.tool()
def read_book(
    book_id: str,
    translated: bool = True,
    max_chars: int = 50000,
) -> str:
    """Read the extracted text content of a book from the library.

    Returns the book's content as markdown text, ready for analysis.
    For non-English books, returns the English translation by default.

    Args:
        book_id: The book's library ID (from list_library or download_book).
        translated: If True, prefer the English translation when available.
        max_chars: Maximum characters to return (0 = unlimited).
                   Default 50000 (~12k tokens). Use 0 for full text.

    Returns:
        The book's content as markdown text.
    """
    book = get_book(book_id)
    if not book:
        return json.dumps({"error": f"Book '{book_id}' not found in library."})

    content = get_book_content(book_id, translated=translated, max_chars=max_chars)
    if not content:
        return json.dumps({
            "error": "No extracted text available for this book.",
            "hint": "The book may not have been processed yet, or text extraction may have failed.",
        })

    return content


@mcp.tool()
def search_book_content(query: str, max_results: int = 10) -> str:
    """Full-text search across all books in the research library.

    Searches through the extracted text of all downloaded books and returns
    matching excerpts with context. Useful for finding specific information
    across your research materials.

    Args:
        query: Text to search for across all books.
        max_results: Maximum number of books to return matches from.

    Returns:
        JSON with matching books and relevant text excerpts.
    """
    results = search_library(query, max_results=max_results)

    if not results:
        return json.dumps({
            "results": [],
            "message": f"No matches for '{query}' across library books.",
        })

    return json.dumps({
        "results": results,
        "count": len(results),
        "query": query,
    }, ensure_ascii=False)


@mcp.tool()
def summarize_book(
    book_id: str,
    focus: str = "",
) -> str:
    """Get instructions and content for summarizing a book.

    Returns the book's content along with instructions for writing a clean,
    detailed research summary. After you generate the summary, call
    save_book_summary to save it as Markdown and PDF.

    The instructions include stop-slop rules to ensure the summary reads
    like natural, human-written prose — not AI-generated text.

    Args:
        book_id: The book's library ID.
        focus: Optional focus area (e.g. "artillery tactics",
               "economic impacts"). Leave empty for a general summary.

    Returns:
        A prompt with the book content and summary instructions.
        Generate the summary from this, then call save_book_summary.
    """
    from .summarizer import get_summary_prompt

    result = get_summary_prompt(book_id, focus=focus)

    if "error" in result:
        return json.dumps(result)

    return result["prompt"]


@mcp.tool()
def summarize_topic(
    topic: str,
    book_ids: list[str],
    focus: str = "",
) -> str:
    """Get instructions for synthesizing multiple books into a topic summary.

    Combines content from multiple books and provides instructions for
    writing a unified research brief. After generating the summary,
    call save_topic_summary to save it.

    Args:
        topic: The research topic (e.g. "Napoleonic cavalry tactics").
        book_ids: List of book IDs to synthesize.
        focus: Optional specific focus within the topic.

    Returns:
        A prompt with combined book content and synthesis instructions.
    """
    from .summarizer import get_topic_summary_prompt

    result = get_topic_summary_prompt(book_ids, topic, focus=focus)

    if "error" in result:
        return json.dumps(result)

    return result["prompt"]


@mcp.tool()
def save_book_summary(
    book_id: str,
    summary_text: str,
    generate_pdf: bool = True,
) -> str:
    """Save a generated summary for a book.

    Saves the summary as Markdown and generates a polished PDF
    with a professional cover page and formatting.

    Call this after generating a summary from summarize_book.

    Args:
        book_id: The book's library ID.
        summary_text: The Markdown summary text you generated.
        generate_pdf: Whether to also create a PDF version (default True).

    Returns:
        JSON with paths to the saved summary files.
    """
    from .summarizer import save_summary

    result = save_summary(
        book_id=book_id,
        summary_text=summary_text,
        generate_pdf=generate_pdf,
    )

    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def save_research_brief(
    topic: str,
    book_ids: list[str],
    summary_text: str,
    generate_pdf: bool = True,
) -> str:
    """Save a cross-book topic research brief.

    Saves a synthesized summary covering multiple books on a topic.
    Generates both Markdown and PDF versions.

    Call this after generating a summary from summarize_topic.

    Args:
        topic: The research topic title.
        book_ids: List of book IDs that were synthesized.
        summary_text: The Markdown summary text you generated.
        generate_pdf: Whether to create a PDF version (default True).

    Returns:
        JSON with paths to the saved files.
    """
    from .summarizer import save_topic_summary

    result = save_topic_summary(
        topic=topic,
        book_ids=book_ids,
        summary_text=summary_text,
        generate_pdf=generate_pdf,
    )

    return json.dumps(result, ensure_ascii=False)


def run_server():
    """Start the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run_server()
