"""Download management for BookFinder."""

import os
import re
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup

from .config import DOWNLOAD_DIR, HEADERS, MAX_RETRIES, REQUEST_TIMEOUT


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
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # LibGen mirror pages have a GET link
        get_link = soup.find("a", string=re.compile(r"GET", re.IGNORECASE))
        if get_link and get_link.get("href"):
            href = get_link["href"]
            if not href.startswith("http"):
                # Relative URL
                from urllib.parse import urljoin
                href = urljoin(url, href)
            return href

        # Alternative: look for direct download links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(ext in href.lower() for ext in [".pdf", ".epub", ".mobi", ".djvu"]):
                if not href.startswith("http"):
                    from urllib.parse import urljoin
                    href = urljoin(url, href)
                return href

    except Exception:
        pass
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
            resp = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT * 2,
                stream=True,
                allow_redirects=True,
            )
            resp.raise_for_status()

            filename = _get_filename_from_response(resp, fallback_name)
            filepath = os.path.join(download_dir, filename)

            # Don't re-download if file exists with same size
            total_size = int(resp.headers.get("content-length", 0))
            if os.path.exists(filepath) and total_size > 0:
                existing_size = os.path.getsize(filepath)
                if existing_size == total_size:
                    return filepath

            downloaded = 0
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            # Verify we got something
            if os.path.getsize(filepath) > 0:
                return filepath
            else:
                os.remove(filepath)

        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            continue
        except Exception:
            break

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

    Returns path to downloaded file, or None if all links fail.
    """
    for link in links:
        result = download_file(
            url=link["url"],
            title=title,
            extension=extension,
            download_dir=download_dir,
            progress_callback=progress_callback,
        )
        if result:
            return result
    return None
