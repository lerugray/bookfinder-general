"""
im-003 quota-reset retry — Lot 49 + Earth Will Shake EPUB upgrade
Run with: .venv/bin/python im003_retry.py

Attempts:
1. Crying of Lot 49 by md5 50e597 or 03eb0a (quota-retry)
2. Earth Will Shake EPUB upgrade (current ingest is OCR-PDF md5=47ebea41;
   EPUB editions at 1.2MB exist — acquire and add WITHOUT removing the PDF)

Does NOT commit or push anything. Leaves all changes in the library only.
"""

import asyncio
import json
import os
import sys
import tempfile

os.environ["BOOKFINDER_LIBRARY"] = "/Users/rayweiss/Desktop/Dev Work/bookfinder-library"

from bookfinder_general.search import search, get_download_links
from bookfinder_general.download import try_download_from_links
from bookfinder_general.library import save_book, list_books, LIBRARY_DIR, generate_book_id

LOG = []


def log(msg):
    print(msg, flush=True)
    LOG.append(msg)


def already_in_library_by_md5(md5_prefix):
    books = list_books()
    for b in books:
        if b.md5 and (b.md5.startswith(md5_prefix[:8]) or md5_prefix[:8] in b.md5):
            return b
    return None


def already_in_library_by_title(fragment):
    books = list_books()
    frag = fragment.lower()
    for b in books:
        if frag in b.title.lower():
            return b
    return None


def get_word_count(book_id):
    p = os.path.join(LIBRARY_DIR, book_id, "content.md")
    if os.path.exists(p):
        with open(p) as f:
            return len(f.read().split())
    return 0


async def try_download_by_md5(md5_prefix, label):
    """Attempt to download a specific md5; return result dict."""
    log(f"\n{'='*60}")
    log(f"[{label}] Attempting direct md5 download: {md5_prefix}")

    # Check already present
    existing = already_in_library_by_md5(md5_prefix)
    if existing:
        wc = get_word_count(existing.id)
        log(f"  Already in library: {existing.id} ({wc:,} words)")
        return {"label": label, "status": "already_present", "book_id": existing.id, "word_count": wc}

    try:
        links = get_download_links(md5_prefix)
    except Exception as e:
        err = str(e)
        log(f"  FAILED getting links: {err}")
        # Distinguish quota/429 from auth/subscription errors
        if "429" in err or "quota" in err.lower() or "daily" in err.lower() or "rate" in err.lower():
            return {"label": label, "status": "quota_429", "error": err}
        elif "401" in err or "403" in err or "auth" in err.lower() or "subscription" in err.lower() or "login" in err.lower():
            return {"label": label, "status": "auth_fail", "error": err}
        else:
            return {"label": label, "status": "link_error", "error": err}

    if not links:
        log(f"  No download links returned (possible quota/subscription gate)")
        return {"label": label, "status": "no_links"}

    log(f"  Got {len(links)} link(s)")
    temp_dir = tempfile.mkdtemp(prefix="im003_")
    log(f"  Downloading...")
    try:
        filepath = try_download_from_links(
            links=links,
            title=label,
            extension="epub",
            download_dir=temp_dir,
        )
    except Exception as e:
        err = str(e)
        log(f"  FAILED download: {err}")
        if "429" in err or "quota" in err.lower():
            return {"label": label, "status": "quota_429", "error": err}
        return {"label": label, "status": "download_error", "error": err}

    if not filepath:
        return {"label": label, "status": "download_failed"}

    file_mb = os.path.getsize(filepath) / (1024 * 1024)
    log(f"  Downloaded {file_mb:.1f}MB")
    log(f"  Saving to library...")

    try:
        entry = save_book(
            filepath=filepath,
            title="The Crying of Lot 49",
            author="Pynchon, Thomas",
            year="1966",
            language="en",
            extension="epub",
            filesize=f"{file_mb:.1f}MB",
            md5=md5_prefix,
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
    return {"label": label, "status": "acquired", "book_id": entry.id, "word_count": wc, "file_mb": round(file_mb, 2)}


async def acquire_earth_will_shake_epub():
    """Upgrade Earth Will Shake from OCR PDF to EPUB edition."""
    label = "Earth Will Shake EPUB upgrade"
    log(f"\n{'='*60}")
    log(f"[{label}] Checking for existing EPUB...")

    # Check if an EPUB version is already present (different md5 than the PDF 47ebea41)
    books = list_books()
    epub_entries = [b for b in books if "earth" in b.title.lower() and "shake" in b.title.lower() and b.extension == "epub"]
    if epub_entries:
        wc = get_word_count(epub_entries[0].id)
        log(f"  EPUB already in library: {epub_entries[0].id} ({wc:,} words)")
        return {"label": label, "status": "already_present", "book_id": epub_entries[0].id, "word_count": wc}

    log(f"  No EPUB yet. Searching Anna's Archive for EPUB editions...")
    results, _ = search("The Earth Will Shake Historical Illuminatus Robert Anton Wilson", ext="epub")

    if not results:
        log(f"  No EPUB results found")
        return {"label": label, "status": "no_results"}

    log(f"  Found {len(results)} results")
    for r in results[:5]:
        log(f"    [{r.extension}] {r.title[:60]} | {r.filesize} | md5={r.md5[:12]}")

    # Pick the best EPUB (prefer ~1.2MB editions per the task note)
    def epub_score(r):
        if (r.extension or "").lower() != "epub":
            return -100
        fs = r.filesize or "0"
        try:
            if "mb" in fs.lower():
                mb = float(fs.lower().replace("mb", "").strip())
            elif "kb" in fs.lower():
                mb = float(fs.lower().replace("kb", "").strip()) / 1024
            else:
                mb = 0
        except:
            mb = 0
        # Prefer 1.0-1.5MB range (the task notes 1.2MB editions)
        if 0.9 <= mb <= 1.6:
            return 10 + mb
        return mb

    epubs = [r for r in results if (r.extension or "").lower() == "epub"]
    if not epubs:
        log(f"  No EPUB format results")
        return {"label": label, "status": "no_epub_format"}

    candidate = max(epubs, key=epub_score)
    log(f"  Selected: {candidate.title[:60]} ({candidate.filesize}) md5={candidate.md5[:12]}")

    # Check if this md5 is already in library
    existing = already_in_library_by_md5(candidate.md5)
    if existing:
        wc = get_word_count(existing.id)
        log(f"  Already in library: {existing.id} ({wc:,} words)")
        return {"label": label, "status": "already_present", "book_id": existing.id, "word_count": wc}

    try:
        links = get_download_links(candidate.md5)
    except Exception as e:
        err = str(e)
        log(f"  FAILED getting links: {err}")
        if "429" in err or "quota" in err.lower():
            return {"label": label, "status": "quota_429", "error": err}
        elif "401" in err or "403" in err or "auth" in err.lower() or "subscription" in err.lower():
            return {"label": label, "status": "auth_fail", "error": err}
        return {"label": label, "status": "link_error", "error": err}

    if not links:
        log(f"  No download links returned")
        return {"label": label, "status": "no_links"}

    log(f"  Got {len(links)} link(s)")
    temp_dir = tempfile.mkdtemp(prefix="im003_ews_")
    log(f"  Downloading...")
    try:
        filepath = try_download_from_links(
            links=links,
            title=candidate.title,
            extension="epub",
            download_dir=temp_dir,
        )
    except Exception as e:
        err = str(e)
        log(f"  FAILED download: {err}")
        if "429" in err or "quota" in err.lower():
            return {"label": label, "status": "quota_429", "error": err}
        return {"label": label, "status": "download_error", "error": err}

    if not filepath:
        return {"label": label, "status": "download_failed"}

    file_mb = os.path.getsize(filepath) / (1024 * 1024)
    log(f"  Downloaded {file_mb:.1f}MB")
    log(f"  Saving to library...")

    try:
        entry = save_book(
            filepath=filepath,
            title=candidate.title,
            author=candidate.author or "Wilson, Robert Anton",
            year=candidate.year or "1983",
            language=candidate.language or "en",
            extension="epub",
            filesize=candidate.filesize or f"{file_mb:.1f}MB",
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
        log(f"  WARNING: Very low word count")

    return {"label": label, "status": "acquired", "book_id": entry.id, "word_count": wc, "file_mb": round(file_mb, 2)}


async def main():
    # Load ANNAS_KEY
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
                log("ANNAS_KEY loaded from settings.json")

    log(f"ANNAS_KEY set: {'yes' if os.environ.get('ANNAS_KEY') else 'no'}")
    log(f"Library: {LIBRARY_DIR}")

    results = []

    # 1. Lot 49 — try md5 50e597 first, then 03eb0a
    log("\n=== STEP 1: Crying of Lot 49 (quota-reset retry) ===")
    r1 = await try_download_by_md5("50e597", "Lot 49 — md5=50e597")
    results.append(r1)
    if r1["status"] not in ("acquired", "already_present"):
        log(f"\n  First md5 failed ({r1['status']}). Trying alternate md5=03eb0a...")
        r1b = await try_download_by_md5("03eb0a", "Lot 49 — md5=03eb0a")
        results.append(r1b)

    # 2. Earth Will Shake EPUB — only if Lot 49 didn't exhaust quota
    lot49_status = r1["status"]
    if r1["status"] not in ("acquired", "already_present"):
        lot49_statuses = [r.get("status") for r in results if "Lot 49" in r.get("label", "")]
        lot49_status = lot49_statuses[-1] if lot49_statuses else "unknown"

    log("\n=== STEP 2: Earth Will Shake EPUB upgrade ===")
    if lot49_status == "quota_429":
        log("  Lot 49 hit quota. Attempting EWS anyway (separate md5, may have different quota behavior)...")
    r2 = await acquire_earth_will_shake_epub()
    results.append(r2)

    # Summary
    log("\n" + "=" * 60)
    log("RETRY SUMMARY")
    log("=" * 60)
    for r in results:
        st = r.get("status", "?")
        wc = r.get("word_count", 0)
        bid = r.get("book_id", "")
        err = r.get("error", "")
        log(f"  {r['label']}: {st} | wc={wc:,} | {bid} | {err[:60] if err else ''}")

    # Save log
    log_path = os.path.join(LIBRARY_DIR, "im003-retry-log.txt")
    with open(log_path, "w") as f:
        f.write("\n".join(LOG))
    log(f"\nLog saved: {log_path}")


if __name__ == "__main__":
    asyncio.run(main())
