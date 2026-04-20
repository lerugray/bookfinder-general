"""Smoke tests for bookfinder-general.

These tests run offline (no network, no Playwright, no Anna's Archive).
They verify: (a) the top-level package imports, (b) the search
relevance-ranking heuristic ranks a known phrase-match first, and
(c) the config module exposes a populated library path constant.

bf-001 seed per GeneralStaff's state/bookfinder-general/tasks.json.
"""

from bookfinder_general import config, search
from bookfinder_general.search import SearchResult, _rank_by_relevance


def _make_result(title: str, author: str = "", language: str = "English") -> SearchResult:
    """Build a minimal SearchResult for ranking tests."""
    return SearchResult(
        title=title,
        author=author,
        publisher="",
        year="",
        language=language,
        extension="",
        filesize="",
        md5="0" * 32,
        url="",
    )


def test_search_module_imports() -> None:
    """The search module imports cleanly without side effects.

    Regression guard for the `from bookfinder_general import search`
    pattern used by the MCP server, CLI, and Flask app. If this fails
    it means search.py's module-level code acquired a dependency that
    isn't in the base `install_requires`, or the package layout broke.
    """
    assert hasattr(search, "search")
    assert hasattr(search, "_rank_by_relevance")
    assert hasattr(search, "SearchResult")


def test_rank_by_relevance_prefers_phrase_match() -> None:
    """_rank_by_relevance ranks an exact-phrase title first.

    Given three titles and the query "python cookbook", the ranking
    should put "Python Cookbook" at position 0 — it's the only title
    where the full query phrase appears, which triggers the 0.3
    phrase bonus on top of the 1.0 match ratio.
    """
    results = [
        _make_result("Cooking with Fire"),           # 0.0 (no query words match)
        _make_result("Python Programming"),          # 0.5 (1 of 2 words)
        _make_result("Python Cookbook"),             # 1.3 (2 of 2 words + phrase bonus)
    ]
    ranked = _rank_by_relevance(results, "python cookbook")
    assert ranked[0].title == "Python Cookbook"


def test_rank_by_relevance_stable_on_empty_query() -> None:
    """_rank_by_relevance is a no-op when the query is all stopwords.

    The function strips short stopwords ("the", "of", "and", etc.)
    and returns the input unchanged if nothing remains. This is a
    correctness boundary — the ranker must not crash on degenerate
    input, since search callers pass arbitrary user queries through.
    """
    results = [_make_result("Anything Goes"), _make_result("Nothing Matters")]
    ranked = _rank_by_relevance(results, "the of and a an")
    assert ranked == results  # same order, same objects


def test_config_library_dir_is_populated() -> None:
    """config.LIBRARY_DIR is a non-empty string.

    The value is derived from the BOOKFINDER_LIBRARY env var with a
    fallback to ~/Research/BookFinder, so it's always populated on
    any platform. DOWNLOAD_DIR is kept as a legacy alias for the web
    UI and should point at the same path.
    """
    assert isinstance(config.LIBRARY_DIR, str)
    assert len(config.LIBRARY_DIR) > 0
    assert config.DOWNLOAD_DIR == config.LIBRARY_DIR
