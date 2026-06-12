"""
Direct EWS EPUB acquisition — try known md5s from the search results.
md5s from im003_retry.py search output:
  3517ac24d4ff  (1.3MB)
  4ab7c086133c  (1.2MB)
  ad8136fcabac  (1.2MB)
  3be0a1364a29  (1.2MB)

Run with: .venv/bin/python im003_ews_direct.py
"""

import asyncio
import json
import os
import sys
import tempfile

os.environ["BOOKFINDER_LIBRARY"] = "/Users/rayweiss/Desktop/Dev Work/bookfinder-library"

from bookfinder_general.search import get_download_links
from bookfinder_general.download import try_download_from_links
from bookfinder_general.library import save_book, list_books, LIBRARY_DIR

LOG = []


def log(msg):
    print(msg, flush=True)
    LOG.append(msg)


def already_in_library_by_md5(md5_prefix):
    books = list_books()
    for b in books:
        if b.md5 and b.md5.startswith(md5_prefix[:8]):
            return b
    return None


def get_word_count(book_id):
    p = os.path.join(LIBRARY_DIR, book_id, "content.md")
    if os.path.exists(p):
        with open(p) as f:
            return len(f.read().split())
    return 0


EWS_MD5S = [
    ("3517ac24d4ff", "Earth Will Shake: Historical Illuminatus Chronicles", "1.3MB"),
    ("4ab7c086133c", "The Earth Will Shake (Historical Illuminatus Chronicles", "1.2MB"),
    ("ad8136fcabac", "The Historical Illuminatus Chronicles -1- The Earth Will Shake", "1.2MB"),
    ("3be0a1364a29", "The Earth Will Shake (Historical Illuminatus Chronicles", "1.2MB"),
]


async def main():
    if not os.environ.get("ANNAS_KEY"):
        settings_path = os.path.expanduser("~/.claude/settings.json")
        if os.path.exists(settings_path):
            with open(settings_path) as f:
                settings = json.load(f)
            key = settings.get("env", {}).get("ANNAS_KEY", "")
            if key:
                os.environ["ANNAS_KEY"] = key
                import importlib
                import bookfinder_general.config as cfg
                import bookfinder_general.search as srch
                importlib.reload(cfg)
                importlib.reload(srch)

    log(f"ANNAS_KEY set: {'yes' if os.environ.get('ANNAS_KEY') else 'no'}")

    for md5_prefix, title_hint, size in EWS_MD5S:
        log(f"\n{'='*60}")
        log(f"Trying EWS md5={md5_prefix} ({size}) — {title_hint[:50]}")

        existing = already_in_library_by_md5(md5_prefix)
        if existing:
            log(f"  Already in library: {existing.id}")
            wc = get_word_count(existing.id)
            log(f"  SUCCESS (already present): {wc:,} words")
            return  # Done

        try:
            links = get_download_links(md5_prefix)
        except Exception as e:
            log(f"  Link error: {e}")
            continue

        if not links:
            log(f"  No links returned, trying next md5...")
            continue

        log(f"  Got {len(links)} link(s)")
        temp_dir = tempfile.mkdtemp(prefix="im003_ews2_")
        try:
            filepath = try_download_from_links(
                links=links,
                title=title_hint,
                extension="epub",
                download_dir=temp_dir,
            )
        except Exception as e:
            log(f"  Download error: {e}")
            continue

        if not filepath:
            log(f"  Download returned no file, trying next md5...")
            continue

        file_mb = os.path.getsize(filepath) / (1024 * 1024)
        log(f"  Downloaded {file_mb:.1f}MB")

        try:
            entry = save_book(
                filepath=filepath,
                title="The Earth Will Shake: Historical Illuminatus Chronicles",
                author="Wilson, Robert Anton",
                year="1982",
                language="en",
                extension="epub",
                filesize=size,
                md5=md5_prefix,
                source_url="",
                extract_text=True,
                translate=False,
            )
        except Exception as e:
            log(f"  Save error: {e}")
            continue

        wc = get_word_count(entry.id)
        log(f"  Saved: {entry.id}")
        log(f"  Word count: {wc:,}")
        if wc < 5000:
            log(f"  WARNING: Low word count")
        else:
            log(f"  SUCCESS: EWS EPUB acquired")

        # Update log
        log_path = os.path.join(LIBRARY_DIR, "im003-retry-log.txt")
        with open(log_path, "a") as f:
            f.write("\n\n=== EWS DIRECT ATTEMPT ===\n")
            f.write("\n".join(LOG))
        return

    log("\n  All EWS md5s exhausted without success")
    log_path = os.path.join(LIBRARY_DIR, "im003-retry-log.txt")
    with open(log_path, "a") as f:
        f.write("\n\n=== EWS DIRECT ATTEMPT ===\n")
        f.write("\n".join(LOG))


if __name__ == "__main__":
    asyncio.run(main())
