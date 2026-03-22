"""Search functionality for Anna's Archive."""

import json
import re
from dataclasses import dataclass
from urllib.parse import quote_plus

import requests

from .config import AA_KEY, HEADERS, MIRRORS, REQUEST_TIMEOUT


@dataclass
class SearchResult:
    """A single search result from Anna's Archive."""
    title: str
    author: str
    publisher: str
    year: str
    language: str
    extension: str
    filesize: str
    md5: str
    url: str
    description: str = ""

    def __str__(self):
        parts = [self.title]
        if self.author:
            parts.append(f"by {self.author}")
        info = []
        if self.year:
            info.append(self.year)
        if self.extension:
            info.append(self.extension.upper())
        if self.filesize:
            info.append(self.filesize)
        if self.language:
            info.append(self.language)
        if info:
            parts.append(f"[{', '.join(info)}]")
        return " ".join(parts)


def _find_working_mirror() -> str:
    """Find the first working mirror (basic connectivity check)."""
    for mirror in MIRRORS:
        try:
            resp = requests.head(mirror, headers=HEADERS, timeout=10, allow_redirects=True)
            if resp.status_code < 500:
                return mirror
        except Exception:
            continue
    return MIRRORS[0]  # Default to first mirror, browser will handle the rest


def search(
    query: str,
    lang: str = "",
    content: str = "",
    ext: str = "",
    sort: str = "",
    page: int = 1,
    mirror: str | None = None,
) -> tuple[list[SearchResult], str]:
    """
    Search Anna's Archive for books using Playwright browser.

    Returns a tuple of (results, mirror_used).
    """
    if mirror is None:
        mirror = _find_working_mirror()

    from .browser import search_page

    html = search_page(
        query=query,
        mirror=mirror,
        lang=lang,
        content=content,
        ext=ext,
        sort=sort,
        page_num=page,
    )

    if not html:
        # Try other mirrors
        for alt_mirror in MIRRORS:
            if alt_mirror == mirror:
                continue
            html = search_page(
                query=query,
                mirror=alt_mirror,
                lang=lang,
                content=content,
                ext=ext,
                sort=sort,
                page_num=page,
            )
            if html:
                mirror = alt_mirror
                break

    if not html:
        raise ConnectionError("Search failed on all mirrors.")

    results = _parse_search_results(html, mirror)
    return results, mirror


def _parse_search_results(html: str, mirror: str) -> list[SearchResult]:
    """Parse search results from Anna's Archive HTML."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    results = []

    # Find result links - Anna's Archive uses a.js-vim-focus for result titles
    result_links = soup.select("a.js-vim-focus")

    if not result_links:
        # Fallback: any link pointing to /md5/
        result_links = soup.find_all("a", href=re.compile(r"/md5/[a-fA-F0-9]+"))

    for link in result_links:
        try:
            href = link.get("href", "")
            md5_match = re.search(r"/md5/([a-fA-F0-9]+)", href)
            if not md5_match:
                continue

            md5 = md5_match.group(1)
            url = f"{mirror}/md5/{md5}"

            # The link text is usually the title
            title = link.get_text(strip=True)

            # The parent container holds metadata
            # Walk up to find the enclosing result div
            container = link.find_parent("div", class_=re.compile(r"flex|aarecord"))
            if container is None:
                container = link.parent

            author = ""
            publisher = ""
            year = ""
            language = ""
            extension = ""
            filesize = ""
            description = ""

            if container:
                full_text = container.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in full_text.split("\n") if l.strip()]

                for line in lines:
                    line_lower = line.lower()

                    # File info often appears as "pdf, 5.2MB" or similar
                    for ext_name in ["pdf", "epub", "mobi", "djvu", "azw3", "fb2", "cbr", "cbz", "txt", "doc", "rtf"]:
                        if re.search(rf"\b{ext_name}\b", line_lower):
                            extension = ext_name
                            break

                    size_match = re.search(r"(\d+\.?\d*\s*[KMGT]?B)", line, re.IGNORECASE)
                    if size_match and not filesize:
                        filesize = size_match.group(1)

                    year_match = re.search(r"\b(1[5-9]\d{2}|20[0-2]\d)\b", line)
                    if year_match and not year:
                        year = year_match.group(1)

                    for lang_name in ["English", "Spanish", "French", "German", "Russian",
                                      "Chinese", "Japanese", "Portuguese", "Italian", "Dutch",
                                      "Polish", "Swedish", "Czech", "Latin"]:
                        if lang_name.lower() in line_lower:
                            language = lang_name
                            break

                # Try to find author - often in a separate element
                author_el = container.find("div", class_=re.compile(r"italic|author"))
                if author_el:
                    author = author_el.get_text(strip=True)

                if not author:
                    # Look for text that seems like an author name (not the title, not metadata)
                    for line in lines[1:4]:  # Check lines after title
                        if line == title:
                            continue
                        if re.search(r"\d+\.?\d*\s*[KMGT]?B", line, re.IGNORECASE):
                            continue
                        if any(ext in line.lower() for ext in ["pdf", "epub", "mobi"]):
                            continue
                        if len(line) < 100 and not line[0].isdigit():
                            author = line
                            break

            results.append(SearchResult(
                title=title or "Unknown",
                author=author,
                publisher=publisher,
                year=year,
                language=language,
                extension=extension,
                filesize=filesize,
                md5=md5,
                url=url,
                description=description[:200],
            ))
        except Exception:
            continue

    return results


def get_download_links(md5: str, mirror: str | None = None) -> list[dict]:
    """
    Get download links for a book by MD5 hash.

    If AA_KEY is set, tries the fast download API first.
    Otherwise uses browser to scrape the detail page.
    """
    if mirror is None:
        mirror = _find_working_mirror()

    links = []

    # Try fast download API if we have a key
    # Errors that mean the key/account is broken — no point trying more combos
    FATAL_ERRORS = {"invalid secret key", "not a member", "no downloads left"}

    if AA_KEY:
        import sys
        api_done = False  # Set True when we get a URL or hit a fatal error
        for path_idx in range(3):
            if api_done:
                break
            for domain_idx in range(3):
                if api_done:
                    break
                try:
                    api_url = (
                        f"{mirror}/dyn/api/fast_download.json"
                        f"?md5={md5}&key={AA_KEY}"
                        f"&path_index={path_idx}&domain_index={domain_idx}"
                    )
                    print(f"[bookfinder] Fast API: md5={md5[:12]}... "
                          f"path={path_idx} domain={domain_idx}", file=sys.stderr)
                    resp = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)

                    try:
                        data = resp.json()
                        print(f"[bookfinder] Fast API response: "
                              f"{json.dumps(data, indent=None)[:500]}", file=sys.stderr)
                    except ValueError:
                        print(f"[bookfinder] Fast API non-JSON: {resp.text[:300]}", file=sys.stderr)
                        continue

                    if resp.status_code != 200:
                        continue

                    # Check for fatal errors — stop trying the API entirely
                    if "error" in data:
                        err = data["error"]
                        err_lower = err.lower()
                        print(f"[bookfinder] Fast API error: {err}", file=sys.stderr)
                        if any(fe in err_lower for fe in FATAL_ERRORS):
                            print(f"[bookfinder] Fast API: fatal error, "
                                  f"skipping to fallback mirrors", file=sys.stderr)
                            api_done = True
                        continue

                    if "download_url" in data and data["download_url"]:
                        print(f"[bookfinder] Fast API: got URL "
                              f"(path={path_idx}, domain={domain_idx})", file=sys.stderr)
                        links.append({
                            "url": data["download_url"],
                            "source": f"Anna's Archive (Fast API)",
                        })
                        api_done = True
                    else:
                        print(f"[bookfinder] Fast API: no download_url, "
                              f"keys: {list(data.keys())}", file=sys.stderr)

                except Exception as e:
                    print(f"[bookfinder] Fast API exception: {e}", file=sys.stderr)

    # Also get links from detail page via browser
    from .browser import detail_page

    html = detail_page(md5, mirror)
    if html:
        links.extend(_parse_download_links(html, mirror))

    return links


def _parse_download_links(html: str, mirror: str) -> list[dict]:
    """Parse download links from a book's detail page."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    links = []
    seen_urls = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        # Skip non-download links (search links, viewer links, torrent metadata, etc.)
        if any(skip in href for skip in [
            "/search?", "viewer=1", "no_redirect=1", "short=1",
            "/member_codes", "/torrents", "ipfs://", "ipfs.tech",
            "/ipfs_downloads", "json.php",
        ]):
            continue

        is_download = False
        source = ""

        # LibGen direct file download links
        if re.search(r"libgen\.\w+/file\.php", href) or "library.lol" in href:
            is_download = True
            source = "Library Genesis"
        elif re.search(r"libgen\.\w+/ads\.php", href):
            is_download = True
            source = "Library Genesis"
        elif re.search(r"libgen\.\w+/book/index\.php", href):
            is_download = True
            source = "Library Genesis"
        # Z-Library
        elif "z-lib" in href or "zlibrary" in href:
            is_download = True
            source = "Z-Library"
        # Anna's Archive slow download (free, no key needed)
        elif re.search(r"/slow_download/[a-fA-F0-9]+/\d+/\d+$", href):
            is_download = True
            source = "Anna's Archive (Slow)"
            if not href.startswith("http"):
                href = f"{mirror}{href}"
        # Anna's Archive fast download (first variant only per domain)
        elif re.search(r"/fast_download/[a-fA-F0-9]+/\d+/\d+$", href):
            is_download = True
            source = "Anna's Archive (Fast)"
            if not href.startswith("http"):
                href = f"{mirror}{href}"

        if is_download and href not in seen_urls:
            seen_urls.add(href)
            links.append({"url": href, "source": source})

    return links
