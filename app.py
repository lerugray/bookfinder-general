"""Bookfinder General - Web UI with search, download, and library management."""

import atexit
import json
import os
import threading

from flask import Flask, jsonify, render_template, request

from bookfinder_general.browser import close_browser
from bookfinder_general.config import LIBRARY_DIR
from bookfinder_general.download import try_download_from_links
from bookfinder_general.library import (
    get_book,
    get_book_content,
    list_books,
    save_book,
    search_library,
)
from bookfinder_general.search import get_download_links, search

app = Flask(__name__)

# Track the last working mirror across requests
_last_mirror = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def api_search():
    global _last_mirror

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "No query provided", "results": []})

    lang = request.args.get("lang", "")
    ext = request.args.get("ext", "")
    content = request.args.get("content", "")

    try:
        results, mirror = search(
            query=query, lang=lang, ext=ext, content=content, mirror=_last_mirror,
        )
        _last_mirror = mirror

        return jsonify({
            "results": [
                {
                    "title": r.title,
                    "author": r.author,
                    "year": r.year,
                    "language": r.language,
                    "extension": r.extension,
                    "filesize": r.filesize,
                    "md5": r.md5,
                    "url": r.url,
                    "description": r.description,
                }
                for r in results
            ],
            "mirror": mirror,
        })

    except ConnectionError as e:
        return jsonify({"error": str(e), "results": []})
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}", "results": []})


@app.route("/api/links")
def api_links():
    global _last_mirror

    md5 = request.args.get("md5", "").strip()
    if not md5:
        return jsonify({"error": "No MD5 provided", "links": []})

    try:
        links = get_download_links(md5, mirror=_last_mirror)
        return jsonify({"links": links})
    except ConnectionError as e:
        return jsonify({"error": str(e), "links": []})
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}", "links": []})


@app.route("/api/download", methods=["POST"])
def api_download():
    """Download a book, extract text, translate, and save to library."""
    data = request.get_json()
    if not data or "md5" not in data:
        return jsonify({"error": "No MD5 provided"})

    md5 = data["md5"]
    title = data.get("title", "Unknown")
    author = data.get("author", "")
    year = data.get("year", "")
    language = data.get("language", "")
    extension = data.get("extension", "pdf")

    # Check if already in library
    existing = [b for b in list_books() if b.md5 == md5]
    if existing:
        book = existing[0]
        return jsonify({
            "status": "already_downloaded",
            "book_id": book.id,
            "title": book.title,
            "has_content": book.has_content,
            "has_translation": book.has_translation,
        })

    # Get download links
    try:
        links = get_download_links(md5, mirror=_last_mirror)
    except Exception as e:
        return jsonify({"error": f"Could not get download links: {e}"})

    if not links:
        return jsonify({"error": "No download links found."})

    # Download to temp location
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="bookfinder_")

    filepath = try_download_from_links(
        links=links, title=title, extension=extension, download_dir=temp_dir,
    )

    if not filepath:
        return jsonify({"error": "Download failed — all mirrors were unavailable."})

    # Detect actual extension
    actual_ext = os.path.splitext(filepath)[1].lstrip(".").lower()
    if actual_ext:
        extension = actual_ext

    # Save to library
    try:
        should_translate = language and language.lower() not in ("english", "en")
        entry = save_book(
            filepath=filepath,
            title=title,
            author=author,
            year=year,
            language=language,
            extension=extension,
            filesize="",
            md5=md5,
            source_url=f"annas-archive/md5/{md5}",
            extract_text=True,
            translate=should_translate,
        )
    except Exception as e:
        return jsonify({"error": f"Processing failed: {e}"})

    # Clean up
    try:
        os.remove(filepath)
        os.rmdir(temp_dir)
    except Exception:
        pass

    return jsonify({
        "status": "downloaded",
        "book_id": entry.id,
        "title": entry.title,
        "has_content": entry.has_content,
        "has_translation": entry.has_translation,
        "library_path": entry.dir_path,
    })


@app.route("/api/library")
def api_library():
    """List books in the library."""
    query = request.args.get("q", "")
    books = list_books(query)

    return jsonify({
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
        "library_path": LIBRARY_DIR,
    })


@app.route("/api/library/<book_id>/content")
def api_book_content(book_id):
    """Get extracted text content of a book."""
    translated = request.args.get("translated", "true").lower() == "true"
    content = get_book_content(book_id, translated=translated)

    if content is None:
        return jsonify({"error": "Book not found or no content available."})

    return jsonify({"content": content, "book_id": book_id})


@app.route("/api/library/search")
def api_library_search():
    """Full-text search across library books."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "No query", "results": []})

    results = search_library(query)
    return jsonify({"results": results, "query": query})


atexit.register(close_browser)


if __name__ == "__main__":
    print("\n  Bookfinder General is running!")
    print(f"  Library: {LIBRARY_DIR}")
    print("  Open your browser to: http://localhost:5000\n")
    app.run(debug=False, port=5000)
