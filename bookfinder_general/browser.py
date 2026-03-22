"""Browser-based access to Anna's Archive using Playwright.

All Playwright calls are pinned to a single dedicated thread to avoid
greenlet 'Cannot switch to a different thread' errors when called from
asyncio.to_thread() which dispatches to random pool threads.
"""

import re
import time
import threading
import concurrent.futures

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from .config import AA_KEY, BROWSER_TIMEOUT, MIRRORS


_browser_instance = None
_context_instance = None

# Single dedicated thread for all Playwright operations
_pw_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="playwright")
_pw_lock = threading.Lock()


def _get_browser_and_context() -> tuple[Browser, BrowserContext]:
    """Get or create a persistent browser instance. Must run on the Playwright thread."""
    global _browser_instance, _context_instance

    if _browser_instance is None or not _browser_instance.is_connected():
        pw = sync_playwright().start()
        _browser_instance = pw.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )
        _context_instance = _browser_instance.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        # Set membership cookie if key is available
        if AA_KEY:
            for mirror in MIRRORS:
                domain = mirror.replace("https://", "")
                _context_instance.add_cookies([{
                    "name": "aa_logged_in",
                    "value": AA_KEY,
                    "domain": domain,
                    "path": "/",
                }])

    return _browser_instance, _context_instance


def _wait_for_page_load(page: Page, timeout: int = BROWSER_TIMEOUT):
    """Wait for page content to be available. Fast return once real content loads."""
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
    except Exception:
        pass

    # Quick check — if content is already there, return immediately
    content = page.content()
    if "Verifying" not in content and len(content) > 500:
        return True

    # Cloudflare challenge — wait up to 8 seconds max
    for _ in range(8):
        time.sleep(1)
        content = page.content()
        if "Verifying" not in content and len(content) > 500:
            return True

    return len(page.content()) > 500


def _fetch_page_impl(url: str) -> str:
    """Fetch a page — runs on the Playwright thread."""
    _, context = _get_browser_and_context()
    page = context.new_page()

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
        if _wait_for_page_load(page):
            return page.content()
        return ""
    except Exception:
        return ""
    finally:
        try:
            page.close()
        except Exception:
            pass


def fetch_page(url: str) -> str:
    """Fetch a page using the browser, handling Cloudflare challenges.
    Thread-safe: dispatches to the dedicated Playwright thread."""
    try:
        future = _pw_executor.submit(_fetch_page_impl, url)
        return future.result(timeout=30)  # 30s hard cap
    except Exception:
        return ""


def search_page(query: str, mirror: str, lang: str = "", content: str = "",
                ext: str = "", sort: str = "", page_num: int = 1) -> str:
    """Fetch search results page."""
    from urllib.parse import quote_plus

    params = [f"q={quote_plus(query)}"]
    if lang:
        params.append(f"lang={quote_plus(lang)}")
    if content:
        params.append(f"content={quote_plus(content)}")
    if ext:
        params.append(f"ext={quote_plus(ext)}")
    if sort:
        params.append(f"sort={quote_plus(sort)}")
    if page_num > 1:
        params.append(f"page={page_num}")

    url = f"{mirror}/search?{'&'.join(params)}"
    return fetch_page(url)


def detail_page(md5: str, mirror: str) -> str:
    """Fetch a book detail page by MD5."""
    url = f"{mirror}/md5/{md5}"
    return fetch_page(url)


def browser_download(url: str, download_dir: str, title: str, extension: str) -> str | None:
    """Download a file via browser. Thread-safe: runs on the Playwright thread."""
    try:
        future = _pw_executor.submit(_browser_download_impl, url, download_dir, title, extension)
        return future.result(timeout=60)
    except Exception:
        return None


def _browser_download_impl(url: str, download_dir: str, title: str, extension: str) -> str | None:
    """Browser download implementation — runs on the Playwright thread."""
    import os
    import sys
    from .download import sanitize_filename, _validate_file_bytes

    page = None
    try:
        _, context = _get_browser_and_context()
        page = context.new_page()

        print(f"[bookfinder] Browser download: {url[:100]}", file=sys.stderr)

        with page.expect_download(timeout=30000) as download_info:
            page.goto(url, timeout=30000)
        download = download_info.value

        suggested = download.suggested_filename
        if suggested and "." in suggested:
            filename = sanitize_filename(suggested)
        else:
            filename = sanitize_filename(f"{title}.{extension}")

        filepath = os.path.join(download_dir, filename)
        download.save_as(filepath)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            if _validate_file_bytes(filepath, extension):
                print(f"[bookfinder] Browser download OK: {filepath}", file=sys.stderr)
                return filepath
            else:
                os.remove(filepath)
                print(f"[bookfinder] Browser download failed validation", file=sys.stderr)

    except Exception as e:
        print(f"[bookfinder] Browser download: no download triggered ({e})", file=sys.stderr)
    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass

    return None


def close_browser():
    """Clean up browser resources."""
    global _browser_instance, _context_instance

    def _close():
        global _browser_instance, _context_instance
        if _context_instance:
            try:
                _context_instance.close()
            except Exception:
                pass
            _context_instance = None
        if _browser_instance:
            try:
                _browser_instance.close()
            except Exception:
                pass
            _browser_instance = None

    try:
        future = _pw_executor.submit(_close)
        future.result(timeout=10)
    except Exception:
        pass
