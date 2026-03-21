#!/usr/bin/env python3
"""BookFinder - Search and download research books from Anna's Archive."""

import argparse
import sys

from bookfinder_general.cli import console, do_download, main, print_banner, print_results_table
from bookfinder_general.search import search


def quick_search(query: str, lang: str = "", ext: str = ""):
    """Run a quick search from the command line without the interactive menu."""
    print_banner()
    console.print(f"\n[dim]Searching for:[/] [bold]{query}[/]...")
    console.print("[dim]A browser window will open to handle the search...[/]")

    try:
        results, mirror = search(query=query, lang=lang, ext=ext)
    except ConnectionError as e:
        console.print(f"[red]Connection error: {e}[/]")
        sys.exit(1)
    finally:
        pass  # Browser cleanup handled by atexit or main

    if not results:
        console.print("[yellow]No results found.[/]")
        sys.exit(0)

    console.print(f"\n[green]Found {len(results)} results[/] (via {mirror})\n")
    print_results_table(results)

    from rich.prompt import Confirm
    if Confirm.ask("\nDownload any of these?", default=False):
        do_download(results, mirror)

    from bookfinder_general.browser import close_browser
    close_browser()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BookFinder - Search & download research books")
    parser.add_argument("query", nargs="*", help="Search query (skip interactive menu)")
    parser.add_argument("--lang", default="", help="Language filter (e.g. en, de, fr)")
    parser.add_argument("--ext", default="", help="File extension filter (e.g. pdf, epub)")

    args = parser.parse_args()

    if args.query:
        quick_search(" ".join(args.query), lang=args.lang, ext=args.ext)
    else:
        main()
