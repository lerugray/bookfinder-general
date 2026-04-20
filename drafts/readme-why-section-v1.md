<!--
Draft for README insertion (bf-005). Not published — pending Ray's edit.

Candidate titles (engineer recommends #1):
  1. Why Bookfinder exists
  2. What this actually fixes
  3. The three failures that prompted this
-->

## Why Bookfinder exists

Three specific failures prompted this tool.

First, Anna's Archive search is ranked by a relevance algorithm that matches on author names and incidental keywords as often as on the actual title. Searching "Supplying War Van Creveld" returns an unrelated Patton book on the first page. Searching "Guns of August Tuchman" returns a Chinese translation of something else. Fine if you already know the MD5 — painful if you don't. Bookfinder re-ranks results by query-word overlap in the title before handing them back, so the book you asked for is the book you get.

Second, most PDFs on Anna's Archive are scanned images, not extractable text. `pymupdf4llm` will happily chew on a 40MB image PDF for an hour and return nothing useful. EPUBs, by contrast, are HTML in a zip — they always extract cleanly. So search results are sorted EPUB-first, PDFs over 25MB skip text extraction by default, and the MCP server's tool descriptions tell the calling model to prefer EPUB. Nothing clever; just avoiding the trap.

Third, LLM summaries of non-fiction default to a recognizable boilerplate — "delve into," "it's worth noting," "navigate the complexities." The summarizer ships with [stop-slop](https://github.com/hardikpandya/stop-slop) rules baked into the prompt, which strip most of the obvious tells. Summaries still read like summaries, but they read less like an LLM wrote them.

Bookfinder doesn't do anything Anna's Archive, `pymupdf4llm`, and an LLM can't do on their own. It does the glue work: right result, clean text, readable prose. The MCP server exposes nine tools so any MCP-compatible client can call any step directly, or the whole pipeline end-to-end.
