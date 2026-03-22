"""Browser-based access to Anna's Archive using Playwright."""

import re
import time

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from .config import AA_KEY, BROWSER_TIMEOUT, MIRRORS


_browser_instance = None
_context_instance = None


def _get_browser_and_context() -> tuple[Browser, BrowserContext]:
    """Get or create a persistent browser instance."""
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
    """Wait for Cloudflare challenge to resolve and real content to load."""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass

    # Check if we're still on a challenge page — wait up to 15 seconds
    for _ in range(15):
        content = page.content()
        if "Verifying" not in content and len(content) > 500:
            return True
        time.sleep(1)

    return len(page.content()) > 500


def fetch_page(url: str) -> str:
    """Fetch a page using the browser, handling Cloudflare challenges."""
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


def close_browser():
    """Clean up browser resources."""
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
