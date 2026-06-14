"""
Headless acquisition driver for Müntzer (muntzergeist) + John Brown (osawatomie)
corpus books. Lands everything in the CENTRAL LIBRARY ONLY — does NOT copy
content.md into any persona corpus dir (those repos don't exist yet).

QUOTA GUARDRAIL: AT MOST 6 books total. Prefer EPUB over PDF.

Target books (priority order):
  1. The Collected Works of Thomas Müntzer (Matheson)  [the one Müntzer gap]
  2. John Brown Speaks: Letters and Statements (DeCaro)
       fallback: John Brown Harpers Ferry Provisional Constitution letters speeches
  3. To Purge This Land with Blood (Oates) — John Brown
  4. John Brown, Abolitionist (David Reynolds)
  5. Fire from the Midst of You (DeCaro) — John Brown

Run with: ANNAS_KEY sourced from ~/.generalstaff/.env, then:
  .venv/bin/python acquire_muntzer_johnbrown.py
"""

import asyncio
import os
import sys
import json
import tempfile
from pathlib import Path

# Override library to the shared central path. CENTRAL LIBRARY ONLY.
os.environ["BOOKFINDER_LIBRARY"] = "/Users/rayweiss/Desktop/Dev Work/bookfinder-library"
# Headless Playwright
os.environ["BOOKFINDER_HEADLESS"] = "true"

from bookfinder_general.search import search, get_download_links
from bookfinder_general.download import try_download_from_links
from bookfinder_general.library import (
    save_book, list_books, LIBRARY_DIR,
)
from bookfinder_general.config import AA_KEY
from bookfinder_general.extractor import extract_to_markdown

DOWNLOADS_USED = 0
MAX_DOWNLOADS = 6
LOG = []

TARGETS = [
    {
        "priority": 1,
        "tag": "muntzergeist",
        "label": "The Collected Works of Thomas Müntzer (Matheson)",
        "queries": [
            "The Collected Works of Thomas Müntzer Matheson",
            "Collected Works Thomas Muntzer Matheson",
        ],
        "hint": "collected works muntzer matheson",
        # This edition (Matheson, Collected Works) is distinct from the
        # "Revelation and Revolution: Basic Writings" Müntzer volume already in
        # the library. Dedup must key on the distinctive editor/title token, not
        # just "muntzer" (which would falsely skip this genuine gap).
        "dedup_must_have": ["matheson", "collected works of thomas"],
        "dedup_min_must_have": 1,
        "prefer_epub": True,
    },
    {
        "priority": 2,
        "tag": "osawatomie",
        "label": "John Brown Speaks: Letters and Statements (DeCaro)",
        "queries": [
            "John Brown Speaks Letters and Statements DeCaro",
            "John Brown Speaks Letters Statements",
        ],
        "hint": "john brown speaks letters statements decaro",
        # Distinctive to THIS book — won't collide with Oates / Reynolds / Fire.
        "dedup_must_have": ["john brown speaks"],
        "dedup_min_must_have": 1,
        "prefer_epub": True,
        "fallback_query": "John Brown Harpers Ferry Provisional Constitution letters speeches",
        "fallback_hint": "john brown harpers ferry constitution letters speeches",
        "fallback_label": "John Brown Harpers Ferry letters/speeches (fallback)",
    },
    {
        "priority": 3,
        "tag": "osawatomie",
        "label": "To Purge This Land with Blood (Oates)",
        "queries": [
            "To Purge This Land with Blood John Brown Oates",
            "To Purge This Land with Blood Oates",
        ],
        "hint": "purge this land with blood john brown oates",
        "dedup_must_have": ["purge this land"],
        "dedup_min_must_have": 1,
        "prefer_epub": True,
    },
    {
        "priority": 4,
        "tag": "osawatomie",
        "label": "John Brown, Abolitionist (David Reynolds)",
        "queries": [
            "John Brown Abolitionist David Reynolds",
            "John Brown Abolitionist Reynolds 2005",
        ],
        "hint": "john brown abolitionist reynolds",
        "dedup_must_have": ["john brown, abolitionist", "john brown abolitionist"],
        "dedup_min_must_have": 1,
        "prefer_epub": True,
    },
    {
        "priority": 5,
        "tag": "osawatomie",
        "label": "Fire from the Midst of You (DeCaro)",
        "queries": [
            "Fire from the Midst of You John Brown DeCaro",
            "Fire from the Midst of You DeCaro",
        ],
        "hint": "fire from the midst of you john brown decaro",
        "dedup_must_have": ["fire from the midst"],
        "dedup_min_must_have": 1,
        "prefer_epub": True,
    },
]


def log(msg):
    print(msg, flush=True)
    LOG.append(msg)


def already_in_library_by_md5(md5):
    for b in list_books():
        if b.md5 == md5 or (md5 and b.md5.startswith(md5[:8])):
            return b
    return None


def already_in_library_by_title(title_fragment):
    fragment = title_fragment.lower()
    for b in list_books():
        if fragment in b.title.lower():
            return b
    return None


def get_word_count(book_id):
    p = Path(LIBRARY_DIR) / book_id / "content.md"
    if p.exists():
        return len(p.read_text(errors="replace").split())
    return 0


_STOP = {"the", "of", "and", "a", "an", "in", "to", "for", "by", "on", "at",
         "is", "it", "with", "from", "this"}


def relevance(r, hint_words):
    """Fraction of (non-stopword) hint words that appear in title+author.
    This is the GATE: an irrelevant book (Carlyle, Minecraft) scores near 0
    even if it's an epub, so it never gets selected over a relevant PDF."""
    combined = (r.title.lower() + " " + (r.author or "").lower())
    sig = [w for w in hint_words if w not in _STOP and len(w) > 2]
    if not sig:
        return 0.0
    hits = sum(1 for w in sig if w in combined)
    return hits / len(sig)


def _size_score(filesize):
    fs = (filesize or "0").lower()
    try:
        if "mb" in fs:
            sz = float(fs.replace("mb", "").strip())
        elif "kb" in fs:
            sz = float(fs.replace("kb", "").strip()) / 1024
        else:
            sz = 0
    except Exception:
        sz = 0
    # tiny files (stub/placeholder bytes) are penalized
    if 0 < sz < 0.1:
        sz -= 5
    return min(sz, 5)


def score_candidate(r, hint_words, prefer_epub):
    """Relevance-first score. Relevance dominates (×100) so a relevant PDF
    always beats an irrelevant epub; epub preference + size only break ties
    among comparably-relevant results."""
    rel = relevance(r, hint_words)
    epub_bonus = 5 if (r.extension or "").lower() == "epub" and prefer_epub else 0
    return rel * 100 + epub_bonus + _size_score(r.filesize)


def find_existing_dup(target):
    """Return an existing library entry only if its title contains the required
    number of distinctive dedup tokens (author surname / distinctive title
    phrase). Avoids matching generic words like 'collected works'."""
    must_have = [t.lower() for t in target.get("dedup_must_have", [])]
    if not must_have:
        return None
    min_needed = target.get("dedup_min_must_have", 1)
    for b in list_books():
        et = b.title.lower()
        hits = sum(1 for t in must_have if t in et)
        if hits >= min_needed:
            return b
    return None


async def acquire_book(target):
    global DOWNLOADS_USED
    label = target["label"]
    tag = target["tag"]
    prefer_epub = target.get("prefer_epub", True)

    log(f"\n{'='*60}")
    log(f"[P{target['priority']}] {label}  (tag: {tag})")

    # Library dedup check by distinctive tokens (author / distinctive phrase)
    existing = find_existing_dup(target)
    if existing:
        wc = get_word_count(existing.id)
        log(f"  Already in library: {existing.id} ({wc:,} words)")
        return {
            "label": label, "tag": tag, "status": "already_present",
            "book_id": existing.id, "resolved_title": existing.title,
            "resolved_author": existing.author, "format": existing.extension,
            "word_count": wc, "downloads_charged": 0,
        }

    if DOWNLOADS_USED >= MAX_DOWNLOADS:
        log(f"  QUOTA EXHAUSTED ({DOWNLOADS_USED}/{MAX_DOWNLOADS}) — skipping")
        return {"label": label, "tag": tag, "status": "quota_exhausted"}

    # Try each query
    results_all = []
    for query in list(target["queries"]):
        log(f"  Searching: {query}")
        try:
            ext = "epub" if prefer_epub else ""
            results, _ = search(query, ext=ext)
            if not results and ext:
                results, _ = search(query, ext="")
        except Exception as e:
            log(f"  Search error: {e}")
            results = []
        if results:
            results_all = results
            log(f"  Found {len(results)} result(s) for: {query}")
            for r in results[:5]:
                log(f"    [{r.extension}] {r.title[:60]} | {r.filesize}")
            break
        log(f"  No results.")

    if not results_all and target.get("fallback_query"):
        log(f"  Trying fallback: {target.get('fallback_label')}")
        try:
            results_all, _ = search(target["fallback_query"], ext="epub")
            if not results_all:
                results_all, _ = search(target["fallback_query"], ext="")
        except Exception as e:
            log(f"  Fallback search error: {e}")
            results_all = []
        if results_all:
            target = dict(target)
            target["hint"] = target.get("fallback_hint", target["hint"])
            target["label"] = target.get("fallback_label", target["label"])
            label = target["label"]
            log(f"  Fallback found {len(results_all)} result(s).")
            for r in results_all[:5]:
                log(f"    [{r.extension}] {r.title[:60]} | {r.filesize}")

    if not results_all:
        log(f"  No results from any query. NOT FOUND.")
        return {"label": label, "tag": tag, "status": "not_found"}

    hint_words = set(target["hint"].lower().split())
    MIN_RELEVANCE = target.get("min_relevance", 0.5)

    # Relevance gate: keep only results whose title+author covers >= MIN_RELEVANCE
    # of the distinctive hint words. This rejects unrelated epubs (Carlyle,
    # Minecraft) that the old epub-first logic was grabbing.
    relevant = [r for r in results_all if relevance(r, hint_words) >= MIN_RELEVANCE]
    if not relevant:
        best = max(results_all, key=lambda r: relevance(r, hint_words))
        log(f"  No result clears relevance gate (>= {MIN_RELEVANCE:.2f}). "
            f"Best was [{best.extension}] {best.title[:50]} (rel={relevance(best, hint_words):.2f}). NOT FOUND.")
        return {"label": label, "tag": tag, "status": "not_found"}

    # Among relevant results, score_candidate prefers epub + reasonable size.
    candidate = max(relevant, key=lambda r: score_candidate(r, hint_words, prefer_epub))
    # Build a relevance-sorted alternate list for link-fallback below.
    results_all = sorted(relevant, key=lambda r: score_candidate(r, hint_words, prefer_epub), reverse=True)

    log(f"  Selected: [{candidate.extension}] {candidate.title[:60]} ({candidate.filesize}) "
        f"rel={relevance(candidate, hint_words):.2f} md5={candidate.md5[:12]}")

    existing = already_in_library_by_md5(candidate.md5)
    if existing:
        wc = get_word_count(existing.id)
        log(f"  Already in library (md5 match): {existing.id} ({wc:,} words)")
        return {
            "label": label, "tag": tag, "status": "already_present",
            "book_id": existing.id, "resolved_title": existing.title,
            "resolved_author": existing.author, "format": existing.extension,
            "word_count": wc, "downloads_charged": 0,
        }

    # Get download links
    log(f"  Getting download links (AA_KEY={'SET' if AA_KEY else 'NOT SET'}) for md5={candidate.md5[:12]}...")
    try:
        links = get_download_links(candidate.md5)
    except Exception as e:
        log(f"  FAILED getting links: {e}")
        return {"label": label, "tag": tag, "status": "link_error", "error": str(e)}

    if not links:
        log(f"  No links on first candidate. Trying alternates...")
        for alt in results_all[1:8]:
            if alt.md5 == candidate.md5:
                continue
            try:
                links = get_download_links(alt.md5)
                if links:
                    candidate = alt
                    log(f"  Using alternate: {alt.title[:50]} md5={alt.md5[:12]}")
                    break
            except Exception:
                pass
        if not links:
            return {"label": label, "tag": tag, "status": "no_links"}

    if DOWNLOADS_USED >= MAX_DOWNLOADS:
        log(f"  QUOTA EXHAUSTED ({DOWNLOADS_USED}/{MAX_DOWNLOADS}) — skipping download")
        return {"label": label, "tag": tag, "status": "quota_exhausted"}

    log(f"  Got {len(links)} link(s). Downloading... (quota: {DOWNLOADS_USED+1}/{MAX_DOWNLOADS})")
    temp_dir = tempfile.mkdtemp(prefix="acq_mjb_")
    try:
        filepath = try_download_from_links(
            links=links,
            title=candidate.title,
            extension=candidate.extension or "epub",
            download_dir=temp_dir,
        )
    except Exception as e:
        log(f"  FAILED download: {e}")
        return {"label": label, "tag": tag, "status": "download_error", "error": str(e)}

    if not filepath:
        return {"label": label, "tag": tag, "status": "download_failed"}

    DOWNLOADS_USED += 1
    file_mb = os.path.getsize(filepath) / (1024 * 1024)
    log(f"  Downloaded {file_mb:.1f}MB (quota now {DOWNLOADS_USED}/{MAX_DOWNLOADS})")

    log(f"  Saving to central library and extracting text...")
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
        return {"label": label, "tag": tag, "status": "save_error", "error": str(e)}

    wc = get_word_count(entry.id)
    log(f"  Saved: {entry.id}")
    log(f"  Word count: {wc:,}")
    extract_warn = None
    if wc < 5000:
        extract_warn = f"very low word count ({wc:,}) — possible scanned/unextractable"
        log(f"  WARNING: {extract_warn}")

    return {
        "label": label, "tag": tag, "status": "acquired",
        "book_id": entry.id, "resolved_title": candidate.title,
        "resolved_author": candidate.author, "format": candidate.extension,
        "word_count": wc, "file_mb": round(file_mb, 2),
        "extract_warn": extract_warn, "downloads_charged": 1,
    }


async def main():
    log("=" * 60)
    log("Müntzer / John Brown book acquisition (CENTRAL LIBRARY ONLY)")
    log(f"QUOTA GUARDRAIL: max {MAX_DOWNLOADS} downloads")
    log(f"LIBRARY: {LIBRARY_DIR}")
    log(f"AA_KEY: {'SET (' + AA_KEY[:6] + '...)' if AA_KEY else 'NOT SET'}")
    log("=" * 60)

    if not AA_KEY:
        log("FATAL: ANNAS_KEY / AA_KEY not set in environment. Aborting.")
        return []

    results = []
    for target in sorted(TARGETS, key=lambda t: t["priority"]):
        result = await acquire_book(target)
        results.append(result)
        if DOWNLOADS_USED >= MAX_DOWNLOADS:
            log(f"\n[QUOTA] Reached {MAX_DOWNLOADS} downloads. Stopping.")
            for t in TARGETS:
                if t["priority"] > target["priority"]:
                    results.append({
                        "label": t["label"], "tag": t["tag"],
                        "status": "quota_exhausted_skip",
                    })
            break

    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    log(f"Downloads used: {DOWNLOADS_USED}/{MAX_DOWNLOADS}")
    log("")
    for r in results:
        st = r.get("status", "?")
        tag = r.get("tag", "?")
        label = r.get("label", "?")
        if st == "acquired":
            log(f"  [{tag}] ACQUIRED: {label}")
            log(f"    entry: {r.get('book_id')}")
            log(f"    resolved: {r.get('resolved_title','?')[:60]} / {r.get('resolved_author','?')[:30]}")
            log(f"    format: {r.get('format')} | {r.get('word_count', 0):,} words | {r.get('file_mb', '?')}MB")
            if r.get("extract_warn"):
                log(f"    extract WARNING: {r['extract_warn']}")
        elif st == "already_present":
            log(f"  [{tag}] ALREADY IN LIBRARY: {label}")
            log(f"    entry: {r.get('book_id')} | resolved: {r.get('resolved_title','?')[:50]} | {r.get('word_count', 0):,} words")
        elif st == "not_found":
            log(f"  [{tag}] NOT FOUND: {label}")
        elif st in ("quota_exhausted", "quota_exhausted_skip"):
            log(f"  [{tag}] SKIPPED (quota): {label}")
        else:
            log(f"  [{tag}] FAILED ({st}): {label}")
            if r.get("error"):
                log(f"    error: {r['error']}")
    log("")
    log("Central library only — no persona corpus dirs were written.")

    return results


if __name__ == "__main__":
    asyncio.run(main())
