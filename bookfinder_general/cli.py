"""CLI interface for BookFinder."""

import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, DownloadColumn, Progress, TransferSpeedColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from .config import CONTENT_TYPES, DOWNLOAD_DIR, FILE_EXTENSIONS
from .download import ensure_download_dir, try_download_from_links
from .search import SearchResult, get_download_links, search

console = Console()


def print_banner():
    """Print the Bookfinder General header panel to the console.

    Returns:
        None. Output is written to the module-level ``console``.
    """
    banner = Text("Bookfinder General", style="bold cyan")
    console.print(Panel(banner, subtitle="Search & Download Research Books", border_style="cyan"))


def print_results_table(results: list[SearchResult]):
    """Display search results in a formatted table.

    Args:
        results: List of ``SearchResult`` rows to render. An empty list
            produces an empty table (no error).

    Returns:
        None. The table is written to the module-level ``console``.
    """
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Title", min_width=30, max_width=50)
    table.add_column("Author", min_width=15, max_width=25)
    table.add_column("Year", width=6, justify="center")
    table.add_column("Format", width=8, justify="center")
    table.add_column("Size", width=10, justify="right")
    table.add_column("Lang", width=6, justify="center")

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            r.title[:50] if r.title else "Unknown",
            r.author[:25] if r.author else "-",
            r.year or "-",
            r.extension.upper() if r.extension else "-",
            r.filesize or "-",
            r.language[:6] if r.language else "-",
        )

    console.print(table)


def do_search(mirror_hint: str | None = None) -> tuple[list[SearchResult], str | None]:
    """Prompt the user for a query, run the search, and render results.

    Interactively collects a query string and optional filters
    (content type, file extension, language), then calls
    :func:`bookfinder_general.search.search` and prints the hits via
    :func:`print_results_table`.

    Args:
        mirror_hint: Preferred Anna's Archive mirror suffix (for example
            ``"gd"``) to reuse from a previous successful call, or
            ``None`` to let the search layer pick one. On a failed
            search the hint is preserved; on a connection error it is
            cleared so the next attempt re-probes mirrors.

    Returns:
        A ``(results, mirror)`` tuple. ``results`` is the list of
        ``SearchResult`` objects (possibly empty). ``mirror`` is the
        mirror suffix that actually served the request, or the incoming
        ``mirror_hint`` / ``None`` if no search was executed.

    Raises:
        Does not raise. ``ConnectionError`` from the search layer is
        caught and reported to the console.
    """
    query = Prompt.ask("\n[bold cyan]Search query[/]")
    if not query.strip():
        console.print("[yellow]Empty query, try again.[/]")
        return [], mirror_hint

    # Optional filters
    use_filters = Confirm.ask("Apply filters (language/format/content type)?", default=False)

    lang = ""
    ext = ""
    content = ""

    if use_filters:
        console.print("\n[dim]Content types:[/]", ", ".join(f"{k or 'empty'}={v}" for k, v in CONTENT_TYPES.items()))
        content = Prompt.ask("Content type", default="", show_default=True)

        console.print("[dim]File formats:[/]", ", ".join(f"{k or 'empty'}={v}" for k, v in FILE_EXTENSIONS.items()))
        ext = Prompt.ask("File extension", default="", show_default=True)

        lang = Prompt.ask("Language (e.g. en, es, de)", default="", show_default=True)

    console.print(f"\n[dim]Searching for:[/] [bold]{query}[/]...")

    try:
        results, mirror = search(
            query=query,
            lang=lang,
            content=content,
            ext=ext,
            mirror=mirror_hint,
        )
    except ConnectionError as e:
        console.print(f"[red]Connection error: {e}[/]")
        return [], None

    if not results:
        console.print("[yellow]No results found. Try a different query or check your connection.[/]")
        return [], mirror_hint

    console.print(f"\n[green]Found {len(results)} results[/] (via {mirror})\n")
    print_results_table(results)
    return results, mirror


def do_download(results: list[SearchResult], mirror: str | None):
    """Prompt the user to pick results and download them with progress.

    Asks for a comma-separated selection (or ``"all"``) and a target
    directory, resolves download links via
    :func:`bookfinder_general.search.get_download_links`, then streams
    each file with :func:`bookfinder_general.download.try_download_from_links`
    while rendering a Rich progress bar.

    Args:
        results: The list of ``SearchResult`` rows produced by the most
            recent :func:`do_search` call. An empty list short-circuits
            with a warning.
        mirror: Mirror suffix to reuse when fetching download links, or
            ``None`` to let the search layer choose.

    Returns:
        None. Progress, errors, and final filepaths are written to the
        module-level ``console``.

    Raises:
        Does not raise. ``ConnectionError`` while fetching links and
        ``ValueError`` from bad selection parsing are caught and
        reported to the console.
    """
    if not results:
        console.print("[yellow]No results to download from. Run a search first.[/]")
        return

    selection = Prompt.ask(
        "\n[bold cyan]Enter number(s) to download[/] (comma-separated, or 'all')",
        default="1",
    )

    if selection.strip().lower() == "all":
        indices = list(range(len(results)))
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            indices = [i for i in indices if 0 <= i < len(results)]
        except ValueError:
            console.print("[red]Invalid selection.[/]")
            return

    if not indices:
        console.print("[red]No valid selections.[/]")
        return

    # Ask for download directory
    dl_dir = Prompt.ask(
        "[bold cyan]Download directory[/]",
        default=DOWNLOAD_DIR,
    )
    ensure_download_dir(dl_dir)

    for idx in indices:
        result = results[idx]
        console.print(f"\n[bold]Fetching download links for:[/] {result.title}")

        try:
            links = get_download_links(result.md5, mirror=mirror)
        except ConnectionError as e:
            console.print(f"[red]Could not get download links: {e}[/]")
            continue

        if not links:
            console.print("[yellow]No download links found for this book.[/]")
            continue

        # Show available sources
        console.print(f"[dim]Found {len(links)} download source(s):[/]")
        for i, link in enumerate(links, 1):
            console.print(f"  {i}. {link['source']}")

        # Download with progress bar
        ext = result.extension or "pdf"

        with Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Downloading {result.title[:40]}...", total=None)

            def update_progress(downloaded, total):
                if total > 0:
                    progress.update(task, total=total, completed=downloaded)
                else:
                    progress.update(task, completed=downloaded)

            filepath = try_download_from_links(
                links=links,
                title=result.title,
                extension=ext,
                download_dir=dl_dir,
                progress_callback=update_progress,
            )

        if filepath:
            console.print(f"[bold green]Downloaded:[/] {filepath}")
        else:
            console.print(f"[red]Failed to download: {result.title}[/]")
            console.print("[dim]All mirror sources failed. The file may be unavailable.[/]")


def main():
    """Run the interactive Bookfinder CLI until the user quits.

    Prints the banner, reports whether an ``ANNAS_KEY`` membership key
    is set, then enters a prompt loop offering search (``s``), download
    (``d``), repeat-last-results (``r``), and quit (``q``). The loop
    keeps the most recent results and mirror in memory so ``d`` / ``r``
    can reuse them.

    Returns:
        None. Exits normally on ``q`` or when stdin closes. On exit the
        shared Playwright browser is closed via
        :func:`bookfinder_general.browser.close_browser`.

    Raises:
        Does not raise for expected flow. ``KeyboardInterrupt`` and
        other unexpected exceptions propagate to the caller after the
        ``finally`` block closes the browser.
    """
    print_banner()

    from .config import AA_KEY
    if AA_KEY:
        console.print("[green]Membership key detected — fast downloads enabled.[/]")
    else:
        console.print("[dim]No membership key set. A browser window will open for searches.[/]")
        console.print("[dim]Set ANNAS_KEY env var for faster, headless access.[/]")

    results = []
    mirror = None

    try:
        while True:
            console.print("\n[bold cyan]Commands:[/]")
            console.print("  [bold]s[/] - Search for books")
            console.print("  [bold]d[/] - Download from last results")
            console.print("  [bold]r[/] - Show last results")
            console.print("  [bold]q[/] - Quit")

            choice = Prompt.ask("\n[bold cyan]>[/]", choices=["s", "d", "r", "q"], default="s")

            if choice == "q":
                console.print("[dim]Goodbye![/]")
                break
            elif choice == "s":
                results, mirror = do_search(mirror_hint=mirror)
                if results:
                    if Confirm.ask("\nDownload any of these?", default=False):
                        do_download(results, mirror)
            elif choice == "d":
                do_download(results, mirror)
            elif choice == "r":
                if results:
                    print_results_table(results)
                else:
                    console.print("[yellow]No results yet. Run a search first.[/]")
    finally:
        # Clean up browser on exit
        from .browser import close_browser
        close_browser()
