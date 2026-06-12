"""
im-002 corpus acquisition — eschaton-model T3 depth tier
Acquires 6 T3 texts: Lovecraft (PD, already in library), Ulysses (PD),
Crowley Book of Lies (PD), Burroughs Naked Lunch (+Nova Express if easy),
Pynchon Crying of Lot 49, Ishmael Reed Mumbo Jumbo.

PD texts fetched from Gutenberg/Sacred-Texts directly; still create
proper library entries matching the im-001 format.

Run with: .venv/bin/python im002_acquire.py
"""

import asyncio
import json
import os
import sys
import tempfile
import time
import urllib.request
import shutil

# Override library to the custom path
os.environ["BOOKFINDER_LIBRARY"] = "/Users/rayweiss/Desktop/Dev Work/bookfinder-library"

from bookfinder_general.search import search, get_download_links
from bookfinder_general.download import try_download_from_links
from bookfinder_general.library import save_book, list_books, LIBRARY_DIR, generate_book_id, BookEntry, _save_metadata
from bookfinder_general.extractor import extract_to_markdown
from datetime import datetime

LOG = []


def log(msg):
    print(msg, flush=True)
    LOG.append(msg)


def already_in_library_by_md5(md5):
    books = list_books()
    for b in books:
        if b.md5 == md5 or b.md5.startswith(md5[:8]):
            return b
    return None


def already_in_library_by_title(title_fragment):
    books = list_books()
    fragment = title_fragment.lower()
    for b in books:
        if fragment in b.title.lower():
            return b
    return None


def get_word_count(book_id):
    content_path = os.path.join(LIBRARY_DIR, book_id, "content.md")
    if os.path.exists(content_path):
        with open(content_path) as f:
            return len(f.read().split())
    return 0


def download_pd_text(url, dest_path):
    """Download a public domain text from a direct URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    with open(dest_path, "wb") as f:
        f.write(data)
    return len(data)


def save_pd_book(title, author, year, text_content, md5_stub, extension="txt"):
    """Create a library entry for a public domain text downloaded directly."""
    # Build ID
    from bookfinder_general.library import _slugify
    slug = _slugify(title)
    author_slug = _slugify(author.split(",")[0].split(" ")[-1])
    book_id = f"{slug[:50]}-{author_slug}-{md5_stub[:8]}"

    book_dir = os.path.join(LIBRARY_DIR, book_id)
    os.makedirs(book_dir, exist_ok=True)

    # Save original text
    orig_path = os.path.join(book_dir, f"original.{extension}")
    with open(orig_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    # Build content.md with header
    header = f"# {title}\n\n**Author:** {author}\n**Year:** {year}\n**Language:** English\n\n---\n\n"
    content_path = os.path.join(book_dir, "content.md")
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(header + text_content)

    wc = len(text_content.split())

    entry = BookEntry(
        id=book_id,
        title=title,
        author=author,
        year=year,
        language="English",
        extension=extension,
        filesize=f"{len(text_content.encode())//1024}KB",
        md5=md5_stub,
        source_url="",
        downloaded_at=datetime.now().isoformat(),
        original_file=f"original.{extension}",
        has_content=True,
        has_translation=False,
        tags=["public-domain"],
    )
    _save_metadata(entry)
    return entry, wc


async def acquire_via_annas(query, hint, prefer_epub, label):
    """Acquire a book via Anna's Archive search."""
    log(f"\n{'='*60}")
    log(f"[{label}] Searching Anna's Archive: {query}")

    ext = "epub" if prefer_epub else ""
    results, _ = search(query, ext=ext)

    if not results and ext:
        log(f"  No EPUB results, trying any format...")
        results, _ = search(query, ext="")

    if not results:
        log(f"  FAILED: No search results found")
        return {"label": label, "status": "no_results", "query": query}

    log(f"  Found {len(results)} results")
    for r in results[:5]:
        log(f"    [{r.extension}] {r.title[:60]} | {r.filesize}")

    # Score candidates
    hint_words = set(hint.lower().split())
    def score(r):
        title_lower = r.title.lower()
        hint_match = sum(1 for w in hint_words if w in title_lower)
        epub_bonus = 10 if (r.extension or "").lower() == "epub" and prefer_epub else 0
        fs = r.filesize or "0"
        try:
            if "mb" in fs.lower():
                size_score = float(fs.lower().replace("mb", "").strip())
            elif "kb" in fs.lower():
                size_score = float(fs.lower().replace("kb", "").strip()) / 1024
            else:
                size_score = 0
        except:
            size_score = 0
        if size_score > 0 and size_score < 0.1:
            size_score -= 5
        return epub_bonus + hint_match * 3 + min(size_score, 5)

    if prefer_epub:
        epubs = [r for r in results if (r.extension or "").lower() == "epub"]
        candidate = max(epubs, key=score) if epubs else max(results, key=score)
    else:
        candidate = max(results, key=score)

    log(f"  Selected: [{candidate.extension}] {candidate.title[:60]} ({candidate.filesize}) md5={candidate.md5[:12]}")

    # Check library
    existing = already_in_library_by_md5(candidate.md5)
    if existing:
        wc = get_word_count(existing.id)
        log(f"  Already in library: {existing.id} ({wc:,} words)")
        return {"label": label, "status": "already_present", "book_id": existing.id,
                "format": candidate.extension, "word_count": wc}

    # Download links
    log(f"  Getting download links...")
    try:
        links = get_download_links(candidate.md5)
    except Exception as e:
        log(f"  FAILED getting links: {e}")
        return {"label": label, "status": "link_error", "error": str(e)}

    if not links:
        log(f"  No links on first candidate. Trying alternates...")
        for alt in results[1:8]:
            if alt.md5 == candidate.md5:
                continue
            try:
                links = get_download_links(alt.md5)
                if links:
                    candidate = alt
                    log(f"  Using alternate: {alt.title[:50]} md5={alt.md5[:12]}")
                    break
            except:
                pass
        if not links:
            return {"label": label, "status": "no_links"}

    log(f"  Got {len(links)} download link(s)")

    temp_dir = tempfile.mkdtemp(prefix="im002_")
    log(f"  Downloading...")
    try:
        filepath = try_download_from_links(
            links=links,
            title=candidate.title,
            extension=candidate.extension or "epub",
            download_dir=temp_dir,
        )
    except Exception as e:
        log(f"  FAILED download: {e}")
        return {"label": label, "status": "download_error", "error": str(e)}

    if not filepath:
        return {"label": label, "status": "download_failed"}

    file_mb = os.path.getsize(filepath) / (1024 * 1024)
    log(f"  Downloaded {file_mb:.1f}MB")

    log(f"  Saving to library and extracting text...")
    try:
        entry = save_book(
            filepath=filepath,
            title=candidate.title,
            author=candidate.author,
            year=candidate.year or "",
            language=candidate.language or "en",
            extension=candidate.extension or "epub",
            filesize=candidate.filesize or "",
            md5=candidate.md5,
            source_url="",
            extract_text=True,
            translate=False,
        )
    except Exception as e:
        log(f"  FAILED save: {e}")
        return {"label": label, "status": "save_error", "error": str(e)}

    wc = get_word_count(entry.id)
    log(f"  Saved: {entry.id}")
    log(f"  Word count: {wc:,}")

    if wc < 5000:
        log(f"  WARNING: Very low word count — may be scanned/unextractable")

    return {
        "label": label, "status": "acquired", "book_id": entry.id,
        "format": candidate.extension, "word_count": wc,
        "file_mb": round(file_mb, 2),
    }


async def acquire_gutenberg_ulysses():
    """Joyce — Ulysses from Project Gutenberg (PD-US)."""
    label = "2. Joyce — Ulysses"
    log(f"\n{'='*60}")
    log(f"[{label}] Checking library...")

    existing = already_in_library_by_title("ulysses")
    if existing:
        wc = get_word_count(existing.id)
        log(f"  Already in library: {existing.id} ({wc:,} words)")
        return {"label": label, "status": "already_present", "book_id": existing.id,
                "format": existing.extension, "word_count": wc}

    log(f"  Fetching from Project Gutenberg (PG-4300)...")
    url = "https://www.gutenberg.org/cache/epub/4300/pg4300.txt"
    temp_path = tempfile.mktemp(suffix=".txt")
    try:
        size = download_pd_text(url, temp_path)
        log(f"  Downloaded {size//1024}KB")
        with open(temp_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        os.unlink(temp_path)
    except Exception as e:
        log(f"  FAILED download: {e}")
        return {"label": label, "status": "download_error", "error": str(e)}

    # Strip Gutenberg header/footer
    start_markers = ["*** START OF", "ULYSSES\n\n\nby James Joyce"]
    end_markers = ["*** END OF", "End of the Project Gutenberg"]
    for m in start_markers:
        idx = text.find(m)
        if idx != -1:
            # Find end of that line
            nl = text.find("\n", idx)
            if nl != -1:
                text = text[nl + 1:]
            break
    for m in end_markers:
        idx = text.find(m)
        if idx != -1:
            text = text[:idx]
            break
    text = text.strip()

    entry, wc = save_pd_book(
        title="Ulysses",
        author="Joyce, James",
        year="1922",
        text_content=text,
        md5_stub="gutenberg4300",
        extension="txt",
    )
    log(f"  Saved: {entry.id}")
    log(f"  Word count: {wc:,}")
    return {"label": label, "status": "acquired", "book_id": entry.id,
            "format": "txt (Gutenberg)", "word_count": wc}


async def acquire_sacredtexts_crowley():
    """Crowley — The Book of Lies from sacred-texts.com (PD-US, 1912)."""
    label = "3. Crowley — The Book of Lies"
    log(f"\n{'='*60}")
    log(f"[{label}] Checking library...")

    existing = already_in_library_by_title("book of lies")
    if existing:
        wc = get_word_count(existing.id)
        log(f"  Already in library: {existing.id} ({wc:,} words)")
        return {"label": label, "status": "already_present", "book_id": existing.id,
                "format": existing.extension, "word_count": wc}

    log(f"  Fetching from sacred-texts.com...")
    # The Book of Lies full text — sacred-texts hosts it as a single page
    url = "https://sacred-texts.com/oto/bol/index.htm"
    temp_path = tempfile.mktemp(suffix=".html")
    try:
        size = download_pd_text(url, temp_path)
        log(f"  Downloaded index {size//1024}KB")
        with open(temp_path, "r", encoding="utf-8", errors="replace") as f:
            index_html = f.read()
        os.unlink(temp_path)
    except Exception as e:
        log(f"  FAILED fetching index: {e}")
        # Fallback: try Gutenberg search via Anna's
        log(f"  Falling back to Anna's Archive search...")
        return await acquire_via_annas(
            "Crowley Book of Lies 1912 Thelema",
            "book of lies crowley",
            True,
            label,
        )

    # Extract chapter links from index
    import re
    # sacred-texts structure: links like bol01.htm, bol02.htm, etc.
    chapter_links = re.findall(r'href="(bol\w+\.htm)"', index_html, re.IGNORECASE)
    if not chapter_links:
        chapter_links = [f"bol{str(i).zfill(2)}.htm" for i in range(0, 100)]

    base_url = "https://sacred-texts.com/oto/bol/"
    full_text = []
    fetched = 0
    for ch_link in chapter_links[:120]:
        ch_url = base_url + ch_link
        try:
            ch_path = tempfile.mktemp(suffix=".html")
            download_pd_text(ch_url, ch_path)
            with open(ch_path, "r", encoding="utf-8", errors="replace") as f:
                ch_html = f.read()
            os.unlink(ch_path)
            # Strip HTML tags
            clean = re.sub(r"<[^>]+>", " ", ch_html)
            clean = re.sub(r"&nbsp;", " ", clean)
            clean = re.sub(r"&amp;", "&", clean)
            clean = re.sub(r"\s{3,}", "\n\n", clean).strip()
            if clean:
                full_text.append(clean)
            fetched += 1
            time.sleep(0.3)
        except:
            break

    if fetched < 3:
        log(f"  Sacred-texts scrape got only {fetched} chapters — falling back to Anna's Archive")
        return await acquire_via_annas(
            "Crowley Book of Lies 1912 Thelema",
            "book of lies crowley",
            True,
            label,
        )

    combined = "\n\n---\n\n".join(full_text)
    log(f"  Scraped {fetched} chapters from sacred-texts")

    entry, wc = save_pd_book(
        title="The Book of Lies",
        author="Crowley, Aleister",
        year="1912",
        text_content=combined,
        md5_stub="sacredtexts-bol",
        extension="txt",
    )
    log(f"  Saved: {entry.id}")
    log(f"  Word count: {wc:,}")
    return {"label": label, "status": "acquired", "book_id": entry.id,
            "format": "txt (sacred-texts)", "word_count": wc}


TARGETS = [
    # (type, args...)
    # 1. Lovecraft — already in library, check/report only
    ("lovecraft_check",),
    # 2. Joyce — Ulysses (PD-US, Gutenberg)
    ("gutenberg_ulysses",),
    # 3. Crowley — Book of Lies (PD-US, sacred-texts)
    ("sacredtexts_crowley",),
    # 4. Burroughs — Naked Lunch (+ Nova Express as secondary)
    ("annas", "Burroughs Naked Lunch Grove Press", "naked lunch burroughs", True, "4. Burroughs — Naked Lunch"),
    # 5. Pynchon — The Crying of Lot 49
    ("annas", "Pynchon Crying of Lot 49", "crying lot 49 pynchon", True, "5. Pynchon — The Crying of Lot 49"),
    # 6. Ishmael Reed — Mumbo Jumbo
    ("annas", "Ishmael Reed Mumbo Jumbo", "mumbo jumbo reed", True, "6. Reed — Mumbo Jumbo"),
]


async def main():
    log("im-002 corpus acquisition — eschaton T3")
    log(f"Library: {LIBRARY_DIR}")

    # Load ANNAS_KEY from settings if not set
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
                log(f"ANNAS_KEY loaded from settings.json")

    log(f"ANNAS_KEY set: {'yes' if os.environ.get('ANNAS_KEY') else 'no'}")

    results = []

    for target in TARGETS:
        ttype = target[0]

        if ttype == "lovecraft_check":
            label = "1. Lovecraft — Complete Fiction"
            log(f"\n{'='*60}")
            log(f"[{label}] Checking library...")
            existing = already_in_library_by_title("lovecraft")
            if existing:
                wc = get_word_count(existing.id)
                log(f"  Found: {existing.id}")
                log(f"  Word count: {wc:,}")
                results.append({"label": label, "status": "already_present",
                                "book_id": existing.id, "format": existing.extension,
                                "word_count": wc})
            else:
                log(f"  NOT FOUND in library — will acquire via Anna's Archive")
                r = await acquire_via_annas(
                    "Lovecraft complete fiction collected works stories",
                    "lovecraft complete",
                    False,
                    label,
                )
                results.append(r)

        elif ttype == "gutenberg_ulysses":
            r = await acquire_gutenberg_ulysses()
            results.append(r)
            if r.get("status") == "acquired":
                await asyncio.sleep(2)

        elif ttype == "sacredtexts_crowley":
            r = await acquire_sacredtexts_crowley()
            results.append(r)
            if r.get("status") == "acquired":
                await asyncio.sleep(2)

        elif ttype == "annas":
            _, query, hint, prefer_epub, label = target
            r = await acquire_via_annas(query, hint, prefer_epub, label)
            results.append(r)
            if r.get("status") == "acquired":
                log("  Pausing 3s before next...")
                await asyncio.sleep(3)
            else:
                await asyncio.sleep(1)

    # Bonus: Nova Express (secondary, only if Naked Lunch succeeded)
    nl_ok = any(r.get("label", "").startswith("4.") and r.get("status") in ("acquired", "already_present")
                for r in results)
    if nl_ok:
        log(f"\n{'='*60}")
        log("[Bonus] Trying Nova Express (Burroughs secondary)...")
        existing = already_in_library_by_title("nova express")
        if existing:
            wc = get_word_count(existing.id)
            log(f"  Already in library: {existing.id} ({wc:,} words)")
            results.append({"label": "Bonus: Burroughs — Nova Express", "status": "already_present",
                            "book_id": existing.id, "format": existing.extension, "word_count": wc})
        else:
            r = await acquire_via_annas(
                "Burroughs Nova Express Grove Press", "nova express burroughs", True,
                "Bonus: Burroughs — Nova Express"
            )
            results.append(r)

    # Summary
    log("\n" + "=" * 60)
    log("ACQUISITION SUMMARY")
    log("=" * 60)

    total_words = 0
    acquired = 0
    gaps = []

    for r in results:
        status = r.get("status", "?")
        wc = r.get("word_count", 0)
        if status in ("acquired", "already_present"):
            acquired += 1
            total_words += wc
            log(f"  OK  {r['label']}: {r.get('format', '?').upper()} | {wc:>8,} words | {r.get('book_id', '?')}")
        else:
            gaps.append(r)
            log(f"  GAP {r['label']}: {status} — {r.get('error', r.get('query', ''))}")

    log(f"\nAcquired: {acquired}/{len(results)}")
    log(f"Total words: {total_words:,}")
    log(f"Gaps: {len(gaps)}")

    # Save log
    log_path = os.path.join(LIBRARY_DIR, "im002-acquisition-log.txt")
    with open(log_path, "w") as f:
        f.write("\n".join(LOG))
    log(f"\nLog saved: {log_path}")


if __name__ == "__main__":
    asyncio.run(main())
