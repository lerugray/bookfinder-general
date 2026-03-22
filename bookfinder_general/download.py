"""Download management for BookFinder."""

import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup

from .config import DOWNLOAD_DIR, HEADERS, MAX_RETRIES, REQUEST_TIMEOUT

# Magic bytes for validating downloaded files
MAGIC_BYTES = {
    "pdf": b"%PDF",
    "epub": b"PK",       # EPUB is a ZIP container
    "mobi": b"BOOKMOBI",
    "djvu": b"AT&TFORM",
    "cbz": b"PK",        # CBZ is also ZIP
    "cbr": b"Rar",       # CBR is RAR
}


def _validate_file_bytes(filepath: str, extension: str) -> bool:
    """Check if a downloaded file has valid magic bytes for its type."""
    try:
        with open(filepath, "rb") as f:
            head = f.read(256)
    except OSError:
        return False

    if not head:
        return False

    # Reject HTML masquerading as a file
    stripped = head.lstrip()
    if stripped[:15].lower().startswith((b"<!doctype", b"<html", b"<head")):
        print(f"[bookfinder] REJECT: File is HTML, not {extension}: {filepath}", file=sys.stderr)
        return False

    # Positive check: verify expected magic bytes
    expected = MAGIC_BYTES.get(extension.lower())
    if expected and not head.startswith(expected):
        print(f"[bookfinder] REJECT: Bad magic bytes for {extension} "
              f"(got {head[:8]!r}, expected {expected!r}): {filepath}", file=sys.stderr)
        return False

    return True


def ensure_download_dir(path: str = DOWNLOAD_DIR) -> str:
    """Create download directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    return path


def sanitize_filename(name: str) -> str:
    """Sanitize a filename for safe filesystem use."""
    # Remove/replace problematic characters
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    # Truncate if too long
    if len(name) > 200:
        base, ext = os.path.splitext(name)
        name = base[:200 - len(ext)] + ext
    return name


def _get_filename_from_response(response: requests.Response, fallback: str) -> str:
    """Extract filename from Content-Disposition header or URL."""
    cd = response.headers.get("Content-Disposition", "")
    if cd:
        # Try to get filename from header
        fname_match = re.search(r'filename[*]?=["\']?(?:UTF-8\'\')?([^"\';\r\n]+)', cd, re.IGNORECASE)
        if fname_match:
            return sanitize_filename(unquote(fname_match.group(1)))

    # Try to get from URL
    parsed = urlparse(str(response.url))
    url_path = unquote(parsed.path)
    if "." in url_path.split("/")[-1]:
        return sanitize_filename(url_path.split("/")[-1])

    return sanitize_filename(fallback)


def _resolve_libgen_link(url: str) -> str | None:
    """Follow a Library Genesis mirror link to get the actual download URL."""
    from urllib.parse import urljoin

    try:
        print(f"[bookfinder] Resolving LibGen link: {url[:80]}", file=sys.stderr)
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # LibGen mirror pages have a GET link (library.lol style)
        get_link = soup.find("a", string=re.compile(r"GET", re.IGNORECASE))
        if get_link and get_link.get("href"):
            href = get_link["href"]
            if not href.startswith("http"):
                href = urljoin(url, href)
            print(f"[bookfinder] LibGen resolved (GET link): {href[:80]}", file=sys.stderr)
            return href

        # LibGen.li/ads.php style — look for the download link in an H2 or heading
        h2_link = soup.select_one("h2 a[href]")
        if h2_link:
            href = h2_link["href"]
            if not href.startswith("http"):
                href = urljoin(url, href)
            print(f"[bookfinder] LibGen resolved (H2 link): {href[:80]}", file=sys.stderr)
            return href

        # Look for direct file links by extension
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(ext in href.lower() for ext in [".pdf", ".epub", ".mobi", ".djvu"]):
                if not href.startswith("http"):
                    href = urljoin(url, href)
                print(f"[bookfinder] LibGen resolved (file ext link): {href[:80]}", file=sys.stderr)
                return href

        # Last resort: any link with "get" or "download" in its text
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True).lower()
            if any(kw in text for kw in ["download", "get", "скачать"]):
                href = a["href"]
                if not href.startswith("http"):
                    href = urljoin(url, href)
                print(f"[bookfinder] LibGen resolved (keyword link): {href[:80]}", file=sys.stderr)
                return href

        print(f"[bookfinder] LibGen: no download link found on page", file=sys.stderr)
    except Exception as e:
        print(f"[bookfinder] LibGen resolve error: {e}", file=sys.stderr)
    return None


def download_file(
    url: str,
    title: str,
    extension: str = "pdf",
    download_dir: str = DOWNLOAD_DIR,
    progress_callback=None,
) -> str | None:
    """
    Download a file from a URL.

    Args:
        url: Direct download URL
        title: Book title (used for filename)
        extension: File extension
        download_dir: Where to save the file
        progress_callback: Called with (downloaded_bytes, total_bytes) during download

    Returns:
        Path to downloaded file, or None on failure.
    """
    ensure_download_dir(download_dir)

    # If it's a libgen mirror link, resolve the actual download URL
    if "library.lol" in url or "libgen" in url:
        resolved = _resolve_libgen_link(url)
        if resolved:
            url = resolved

    fallback_name = f"{title}.{extension}" if not title.endswith(f".{extension}") else title

    for attempt in range(MAX_RETRIES):
        try:
            print(f"[bookfinder] Downloading (attempt {attempt+1}/{MAX_RETRIES}): {url[:100]}", file=sys.stderr)
            resp = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT * 2,
                stream=True,
                allow_redirects=True,
            )
            resp.raise_for_status()

            # Reject HTML responses — means we got a paywall/error page
            content_type = resp.headers.get("content-type", "").lower()
            if "text/html" in content_type:
                print(f"[bookfinder] Got HTML content-type from {url[:80]}...", file=sys.stderr)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                continue

            filename = _get_filename_from_response(resp, fallback_name)
            filepath = os.path.join(download_dir, filename)

            # Don't re-download if file exists with same size
            total_size = int(resp.headers.get("content-length", 0))
            if os.path.exists(filepath) and total_size > 0:
                existing_size = os.path.getsize(filepath)
                if existing_size == total_size and _validate_file_bytes(filepath, extension):
                    print(f"[bookfinder] Already downloaded (valid): {filepath}", file=sys.stderr)
                    return filepath

            downloaded = 0
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            # Validate the downloaded file
            fsize = os.path.getsize(filepath)
            if fsize > 0 and _validate_file_bytes(filepath, extension):
                print(f"[bookfinder] Download OK: {filepath} ({fsize:,} bytes)", file=sys.stderr)
                return filepath
            else:
                if os.path.exists(filepath):
                    os.remove(filepath)
                print(f"[bookfinder] Download failed validation, removed: {filepath}", file=sys.stderr)

        except requests.RequestException as e:
            print(f"[bookfinder] Request error: {e}", file=sys.stderr)
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            continue
        except Exception as e:
            print(f"[bookfinder] Unexpected error: {e}", file=sys.stderr)
            break

    return None


def _browser_download(
    url: str,
    title: str,
    extension: str,
    download_dir: str,
) -> str | None:
    """Download a file using Playwright browser (handles Cloudflare, cookies, JS redirects)."""
    try:
        from .browser import _get_browser_and_context
        import tempfile

        print(f"[bookfinder] Trying browser download: {url[:100]}", file=sys.stderr)
        _, context = _get_browser_and_context()

        # Use a temporary download dir so Playwright can manage the download
        with tempfile.TemporaryDirectory() as tmp_dir:
            page = context.new_page()
            try:
                # Start a download by navigating to the URL
                with page.expect_download(timeout=120000) as download_info:
                    page.goto(url, timeout=60000)
                download = download_info.value

                # Save to a temp path first
                suggested = download.suggested_filename
                if suggested and "." in suggested:
                    filename = sanitize_filename(suggested)
                else:
                    filename = sanitize_filename(f"{title}.{extension}")

                filepath = os.path.join(download_dir, filename)
                download.save_as(filepath)

                # Validate
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    if _validate_file_bytes(filepath, extension):
                        print(f"[bookfinder] Browser download OK: {filepath}", file=sys.stderr)
                        return filepath
                    else:
                        os.remove(filepath)
                        print(f"[bookfinder] Browser download failed validation", file=sys.stderr)
            except Exception as e:
                print(f"[bookfinder] Browser download error: {e}", file=sys.stderr)
            finally:
                page.close()
    except Exception as e:
        print(f"[bookfinder] Browser download setup error: {e}", file=sys.stderr)

    return None


def try_download_from_links(
    links: list[dict],
    title: str,
    extension: str = "pdf",
    download_dir: str = DOWNLOAD_DIR,
    progress_callback=None,
) -> str | None:
    """
    Try downloading from a list of mirror links, stopping at the first success.
    Falls back to browser-based download if plain HTTP fails for a link.

    Returns path to downloaded file, or None if all links fail.
    """
    ensure_download_dir(download_dir)

    for link in links:
        url = link["url"]
        source = link.get("source", "unknown")
        print(f"[bookfinder] Trying link: {source} — {url[:80]}", file=sys.stderr)

        # First try plain HTTP (fast)
        result = download_file(
            url=url,
            title=title,
            extension=extension,
            download_dir=download_dir,
            progress_callback=progress_callback,
        )
        if result:
            return result

        # If plain HTTP failed, try browser-based download (handles Cloudflare/JS)
        result = _browser_download(
            url=url,
            title=title,
            extension=extension,
            download_dir=download_dir,
        )
        if result:
            return result

    print(f"[bookfinder] All {len(links)} download links failed", file=sys.stderr)
    return None
