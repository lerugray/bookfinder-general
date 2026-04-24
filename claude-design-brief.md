# Bookfinder General — Claude Design Brief

For upload to **claude.ai/design**. Purpose: generate a
`SKILL.md` that anchors the visual + interaction direction of
Bookfinder's web UI — search, results, library, and book-detail
screens. The existing UI (single `templates/index.html`, Flask-
served) is functional but generic dark-mode neon-cyan. This
brief anchors a specific aesthetic so subsequent Claude sessions
extending the UI produce consistent, distinctive output instead
of drifting back toward generic SaaS dark-mode.

---

## What this is

**Bookfinder General** is a research book finder, downloader,
and summarizer. It hunts down books on Anna's Archive (rare,
out-of-print, non-English, academic), downloads them through
mirror fallback, extracts text, auto-translates non-English
material, and generates stop-slop summaries and multi-book
research briefs.

Python 3.11+ / Flask web UI / MCP server / CLI. Users are
researchers, academics, writers, and curious generalists who
know what book they want (or roughly what topic) and need the
tool to surface the right file, clean it up, and hand back
usable text.

Named after the [Witchfinder General](https://en.wikipedia.org/
wiki/Witchfinder_General). Hunts books, not witches. The name
sets tone: this is a **hunting tool**, not a discovery or
browsing tool. Users arrive with intent, not curiosity.

---

## Core product constraint

**Bookfinder is a research utility, not a consumer product.**
The user base is narrow and motivated:

- Knows how to articulate a search (title + author, or topic +
  era)
- Is comfortable reading dense metadata — filesize, extension,
  language, year, source mirror
- Cares about result accuracy (Anna's Archive's native ranking
  is noisy; Bookfinder re-ranks for title relevance)
- Will download, read, summarize, and cite. Does not want to be
  entertained on the way.

The UI should feel like **a research terminal**, not a consumer
app. **Information density over visual polish.** Archival
discipline over friendliness. No onboarding, no empty-state
illustrations, no encouragement-copy, no "Welcome back!"
greeting. Researchers arrive ready to work.

---

## Anchor vibe: library card-catalog × archival research terminal

The aesthetic anchor is the **reference-room computer at a
university library circa 1998-2005** — OPAC terminals, JSTOR
result screens, HathiTrust catalog views, WorldCat search —
but modernized for usability and ergonomics. The feel of
sitting down at a workstation where someone has been serious
about books for a long time.

Specific references:

- **Library OPAC terminals** (Online Public Access Catalog).
  Monospace bibliographic data, field-label-then-value layout,
  unapologetic density. The screen where you search for a book
  and get call number + shelf location + holding status —
  nothing more.
- **JSTOR** (classic, not the 2020+ redesign). Results in
  plain-prose scholarly format: title, author, publication,
  year, abstract. Citation-ready at a glance.
- **HathiTrust Digital Library** result screens. Stark,
  institutional, metadata-forward. No hero images.
- **The Anarchist's Library** (theanarchistlibrary.org). Plain-
  text bibliographic entries. Author → title → date → format.
  This is the closest living reference for the vibe.
- **Project Gutenberg catalog pages**. Sparse, utilitarian,
  browse-by-metadata rather than cover-art. Text-first.

What we are **not** anchoring on:

- Goodreads / Amazon Books (consumer discovery, cover-heavy,
  social-layer)
- Libib / Bookwyrm (personal-library app aesthetic, chat-bubble
  friendliness)
- Notion / Linear / Raycast (general productivity — good bones
  but too neutral; Bookfinder should feel *specifically
  bibliographic*, not generically productive)
- JSTOR's 2020+ redesign or HathiTrust's 2023 refresh (both
  slid toward consumer-accessibility; we want the pre-redesign
  institutional feel)

---

## Tonal anchor: the Witchfinder in the name

The product name carries weight. A Witchfinder woodcut sits
above the README title. That tonal choice should show up in
the UI — not as gimmick or theme-park costume, but as a
**subtle woodcut-era typographic restraint** folded into an
otherwise-modern research tool.

Concretely:

- **The wordmark can carry period weight** (a seriffed, almost
  broadsheet-style title treatment for "Bookfinder General" at
  the top of the UI). The rest of the UI should not be period
  — just the title.
- **Tagline allowed:** *"Hunts books, not witches."* (small,
  italic, under the wordmark). Do not remove the tagline in
  favor of a "Search & Download Research Books" bland
  description. The existing UI made that substitution and it
  erased the product's voice.
- **No witch iconography inside the UI.** The woodcut belongs
  on the README and landing page, not in search results. Don't
  make this a Halloween theme.
- **Severe, not whimsical.** The name is already funny on its
  own terms (Witchfinder General was a real 17th-century
  English witch-hunter named Matthew Hopkins; the name implies
  uncompromising pursuit). The UI should back up that
  implication. No playful emoji, no "Oops, no books found!"
  copy, no animation flourishes.

---

## Visual constraints

### Color

**Dark-mode primary, but not neon.** The existing UI uses
`#1a1a2e` background with `#00d4ff` cyan accents. That cyan
reads as generic SaaS/crypto. Replace with a more
**archival / parchment** accent palette:

- **Background:** deep near-black, very slight warm cast
  (~#0d0d10 to #141418 range). NOT pure black, NOT blue-black.
  A dim reading-room feel.
- **Primary text:** warm off-white (~#e8e4d8 or #ece6d3 — a
  parchment white, not a clinical white). NOT `#ffffff`.
- **Secondary text / metadata:** desaturated tan or aged-paper
  gray (~#8a8474, #a59f8e).
- **Accent — primary:** a muted **amber / ochre** (~#c8a25a,
  #d4a85c, #b8903a) — library-lamp gold, NOT cyan, NOT purple,
  NOT electric blue. Used for: search-bar focus border, active
  tab indicator, link hover, result-count numerals.
- **Accent — danger/error:** a muted **iron oxide red**
  (~#a04848, #9c3b3b) — NOT bright coral, NOT `#ff6b6b`.
- **Accent — success:** an **old-manuscript green**
  (~#6b8e4a, #789a5a) — NOT bright spring green, NOT neon
  mint. Think printer's ink, not CSS `green`.

Light mode is a secondary consideration — if implemented, it
should resemble **a law-library reading room**: warm off-white
paper (~#f4f0e4) with sepia/iron text, not clinical Apple-white.
Do not make light mode a priority; researchers use this at
night.

### Typography

- **Monospace for bibliographic data.** Filesize, extension,
  year, ISBN, MD5 hash, language code, library call-number-style
  IDs. Use a real monospace (IBM Plex Mono, JetBrains Mono, or
  system monospace). This is the single most important
  typographic decision — it signals "real catalog data" rather
  than "styled web content."
- **Serif for the wordmark only.** A single serif line at the
  top (name + tagline). Can be a broadsheet-period serif — Old
  Standard TT, EB Garamond, or similar. Do not use this serif
  elsewhere in the UI.
- **Clean humanist sans for everything else** — titles,
  authors, body copy, buttons. IBM Plex Sans, Inter at a
  restrained weight, or system sans. NOT rounded / friendly
  (no Nunito, no Comic, no Varela). NOT geometric-trendy
  (Avoid Circular, DM Sans's rounder weights).
- **Weight restraint.** Two weights max in the UI: Regular
  (400) and Medium/Semibold (500-600) for hierarchy. No Bold
  900, no Extralight 200, no italic except the tagline and
  foreign-language titles in italic per academic convention.
- **Size discipline.** Bibliographic metadata at 12-13px is
  fine — researchers read catalog data at that size all day.
  Don't upsize for "readability"; dense catalog is the feature.

### Density

- **Padding in 4-6-8-12px increments, not 16-24-32.** This is
  a catalog, not a landing page. Tight rows, scanable columns.
- **Result rows, not cards.** The current UI uses rounded
  cards (`border-radius: 10px`, 16px padding). Cards waste
  vertical space. Switch to **table-like rows** with
  horizontal rules between entries, ~8-10px vertical padding
  per row. A research library result list fits 15-25 entries
  above the fold on a 1080p monitor, not 4-5.
- **Horizontal space is also cheap.** Don't cap content at
  `max-width: 1000px` the way a marketing page would. Catalog
  UIs use the full width — metadata columns fan out to the
  right of the title. Allow the UI to breathe horizontally on
  wide monitors; ~1400-1600px feels right as a soft cap.
- **Whitespace as structural separator, not aesthetic
  breath.** A 16px gap exists because a section ended, not
  because we wanted the layout to feel airy.

### Borders and dividers

- **Hair-line horizontal rules** between result entries
  (`border-bottom: 1px solid #2a2a2a` or similar). Replaces
  rounded-card borders as the structural separator.
- **No box shadows.** No `drop-shadow()`, no `box-shadow`.
  Flat, hard-edged panels. A research terminal does not
  render material depth.
- **Corners at 0-2px radius max.** No `border-radius: 10px
  12px` consumer softness. If rounding is used at all, it's
  2px max. Inputs and buttons: 2px or square.

### Motion

- **Essentially none.** No hover-scale, no slide-in, no fade-
  in on page load. A search submission can show an
  indeterminate progress indicator (see below), and downloads
  can show progress, but layouts do not animate into view.
- **No spinner rings.** The existing cyan spinning ring is
  SaaS-coded. Replace with either a **blinking underscore /
  text cursor** (`|` or `_`) or a **horizontal progress bar**
  that fills as extraction/translation advances. If a spinner
  is kept, make it monochrome and small.
- **Transitions, if any, are 100-150ms linear.** No cubic-
  bezier easing, no 300-500ms swoops.

---

## Functional surface (what the UI needs to show)

### 1. Global layout

- **Top bar:** wordmark ("Bookfinder General" in serif),
  tagline ("Hunts books, not witches."), tab navigation
  (Search / Library / Briefs). Small status indicator showing
  library path + library-entry count (e.g., "~/Research/
  BookFinder · 47 volumes"). Monospace for the count.
- **Main content area:** the active tab's screen.
- **Bottom-right status strip (persistent):** current mirror
  being used (`annas-archive.gl`), last search timing (`search:
  2.3s`), ANNAS_KEY status (`key: set` / `key: none`).
  Monospace, small, neutral-tan color. This is where an
  operator checks for "why is search slow" without leaving
  the result view.

### 2. Search screen

- **Search bar** is a single wide input with a small inline
  submit (arrow or "Search"). Placeholder reads: *"Title,
  author, ISBN, or topic."* — not the current *"Search for
  books... (titles in any language, authors, topics)"* (too
  long, too friendly).
- **Filter row below** the search bar: Language, Format, Type
  (nonfiction/fiction/magazine). The existing UI has these
  correctly — keep the structure, restyle per the visual
  constraints above. Each filter is a compact `<select>` with
  the field label (monospace, uppercase small-caps) *above*
  the control, not to its left.
- **Advanced row (optional disclosure):** year range (from /
  to as two small inputs), size cap (drop PDFs over N MB),
  "prefer EPUB" toggle (on by default per product design).
  Hidden by default behind a small "+ advanced" control —
  expanding it is the only time a disclosure pattern is used
  in the UI.

### 3. Results list

Each result is one row, not a card. Columns (left to right):

- **Title** (primary text, medium weight). Truncated with
  ellipsis if >~80ch; hover reveals full title in a tooltip
  or expansion.
- **Author** (secondary text, regular weight, below or inline
  depending on width).
- **Year** · **Language** · **Format** · **Filesize** — each
  in monospace, 12px, tab-separated visually by thin vertical
  rules (`|`) or ~8px gaps. Example: `1987 · de · EPUB ·
  2.1 MB`.
- **Actions** (right-aligned): `[Download]` `[Links]`
  `[Copy MD5]`. Small, tight, text-only buttons (no filled-
  button drama). Download is the amber-accent action; the
  rest are neutral.

Relevance indicator: an **optional leading marker** for top-
ranked results (e.g., `*` for the top 3 after re-ranking, in
amber). Subtle; a researcher skimming the list should notice
the top match without being shouted at.

Empty state: a single line of text. *"No results. Try the
author's surname plus one keyword from the title."* No
illustration, no encouragement.

### 4. Result detail / expansion

Clicking a result row expands it inline (accordion-style) to
show:

- **Full metadata block** in a monospace field-label layout:
  ```
  TITLE     Der italienische Feldzug von 1859
  AUTHOR    Helmuth von Moltke
  YEAR      1887
  LANGUAGE  de (German)
  FORMAT    PDF
  SIZE      4.2 MB
  MD5       11ca3de1b8f4e9a5c7d2f6e0a8b3c1d4
  SOURCE    annas-archive.gl
  ```
- **Description / abstract** (if available) in sans body
  text, ~2-4 lines.
- **Download links panel** (existing `.download-links`
  structure is fine — restyle per visual constraints).
- **Action row**: `[Download to library]` `[Translate on
  download]` (checkbox) `[Summary after download]`
  (checkbox).

### 5. Library screen

- **Filter input** (small, top-left). No "Filter library..."
  placeholder — just a `/` keyboard-shortcut hint inline.
- **Sort controls** (right of filter): by Date added, Title,
  Author, Year, Language.
- **Library rows** same layout as search results, but with
  different column priorities:
  - **Title + Author** (primary).
  - **Status badges**: `[text]` `[translated]` `[summarized]`
    — small monospace tags in muted colors (not brightly
    colored pills). A book with full text + translation +
    summary shows `[text · translated · summarized]` in one
    run.
  - **Year · Language · Format** (secondary metadata).
  - **Library ID** in monospace, dim, at the row end (e.g.,
    `11ca3de1`). Click to copy.

Empty state: *"Library empty. Search and download to begin."*
One line. The parent CLAUDE.md emphasizes that the library is
meant to be git-synced across machines; a small persistent
hint ("Sync: off — set BOOKFINDER_SYNC=true") belongs in the
bottom-right status strip, not in the library's empty state.

### 6. Book detail view (read-a-book screen)

When the user opens a library book:

- **Top metadata strip** (compressed monospace block): title,
  author, year, language, format, size, library ID. Fixed at
  top while scrolling the content.
- **Content area** showing extracted Markdown. Render
  Markdown with the **same typographic discipline** as the
  rest of the UI (serif is NOT allowed here even though it's
  book content — researchers are reading for information, not
  atmosphere; use the sans body font).
- **Translation toggle** if `content_en.md` exists:
  `[original]` `[translated]` pill-switch, top-right of
  content.
- **Summary tab** if `summary.md` exists.
- **Actions**: `[Generate summary]` `[Add to brief]` `[Open
  in file manager]`.

### 7. Research brief screen (multi-book synthesis)

- **Topic name + books included** at top (list of library
  IDs / titles, editable — remove book from brief, add
  book).
- **Brief content** (rendered Markdown, same typography as
  book detail).
- **Actions**: `[Regenerate]` `[Export PDF]` `[Export
  Markdown]`.

Low priority for v1 — the product ships briefs via MCP tool
today; UI version can be stubbed.

---

## Operator-speed principles

Bookfinder users are researchers, not tourists. The UI should
reward speed:

- **Keyboard shortcuts.** `/` focuses the search input.
  `Esc` clears focus. `Enter` submits. `j` / `k` moves
  selection in the results list (vim-style — researcher
  demographic will recognize this). `o` opens the selected
  result (expand detail). `d` downloads the selected
  result. `l` jumps to library. These should be discoverable
  via a small `?` help modal (one screen, monospace keymap).
- **No loading spinners blocking layout.** A search in
  progress renders a monospace line *"searching
  annas-archive.gl via playwright..."* in the status strip
  (bottom-right). Results appear as they arrive if the
  backend supports streaming; otherwise, show the line until
  complete. The existing spinner on the search button can
  stay as a minor inline affordance but must be monochrome.
- **Filters are URL-param-persistent.** A search with `lang=
  de&ext=epub` survives a page refresh. (Backend handles this
  trivially; the UI just needs to re-populate on load.)
- **Copy-friendly metadata.** Every MD5, library ID, and
  file path should be click-to-copy. No "Copied!" toast —
  just a brief (100ms) dim-highlight flash on the copied
  element. Toasts are consumer-coded.
- **No modal dialogs for confirmations.** A click on
  `[Download]` begins download; status updates in-place on
  the row. No "Are you sure?" — researchers don't need hand-
  holding, and mistakes are undo-able (delete from library).

---

## What the SKILL.md should produce

When a future Claude session opens Bookfinder to build or
extend the web UI, the SKILL should let me:

1. **Reach for the right component vocabulary** — result-row,
   metadata-block, filter-select, status-strip, field-label-
   value pair, download-link panel. Named and patternable,
   not reinvented each screen.
2. **Apply the palette without rederiving** — parchment-white
   text, archival-amber primary accent, iron-oxide error,
   manuscript-green success. The SKILL lists the exact hex
   values and when to use each.
3. **Choose the right typographic register** — monospace for
   catalog data, sans for body, serif only for the wordmark.
   Never mix them the wrong way.
4. **Pattern-match and flag consumer-app drift** — if a
   future session adds rounded-12px cards, a cyan accent, a
   welcome-back banner, or a "Congratulations! You added your
   first book!" toast, the SKILL should catch it as a
   violation.
5. **Know the layout grid** — dense rows over sparse cards,
   full-width content over 1000px-centered columns, 4-6-8-12
   padding over 16-24-32.
6. **Preserve the tonal anchor** — the wordmark's period
   weight, the "hunts books, not witches" tagline, the
   absence of whimsy elsewhere. A future session rewriting
   copy should preserve this voice, not flatten it into
   SaaS-neutral.

---

## Constraints on the SKILL output

- Target **250-500 lines of Markdown**.
- Readable at session start without overwhelming the model —
  dense but structured. Assume the reader is a Claude session
  about to touch `templates/index.html` or spin up a new
  frontend and needs anchoring fast.
- **Include a "Do not / Avoid" section** naming specific
  LLM-default and consumer-app patterns to catch:
  - Rounded cards with drop shadows
  - Cyan / electric-blue accent colors
  - Emoji in UI copy (no book emoji, no magnifying-glass,
    no witch, no sparkles)
  - Hero illustrations or empty-state artwork
  - "Welcome to Bookfinder!" / onboarding flow copy
  - "Congratulations" / celebration toasts after downloads
  - Marketing-site max-width content caps (1000px, 1200px)
    when the screen is 1600+
  - Gradient backgrounds, animated gradients, glass-morphism
  - Tailwind-default spacing rhythm (gap-4, gap-6, gap-8
    everywhere — gives everything a consumer-accessible
    breathiness)
  - "Aa" font-swap buttons, theme-customizer panels (the
    aesthetic is not up for user negotiation)
  - Rounded pill buttons with gradient backgrounds
  - Sidebar nav with 24px icons (this is not Notion)
- **Include per-screen palette callouts** with exact hex
  values: search screen uses X as focus-state accent, library
  uses Y for status badges, detail view uses Z for metadata
  block backgrounds.
- **Include the typographic register rules** as a compact
  table: Monospace (catalog data, IDs, timings, field values),
  Sans (titles, authors, body, buttons, filter labels), Serif
  (wordmark + tagline only, nothing else).
- **Include keyboard shortcut conventions** so future UI
  additions don't stomp them (`/`, `Esc`, `Enter`, `j/k`,
  `o`, `d`, `l`, `?`).
- **Reference the existing `templates/index.html`** as the
  starting point — the SKILL should frame its guidance as
  *"what to change about this file"*, not *"build a new UI
  from scratch."*

---

## Reference anchors

**Visual:**

- OPAC terminal screenshots from 1995-2005 university
  libraries (search "library catalog terminal 1999" or
  "OPAC screenshot")
- JSTOR result screens (pre-2020 redesign)
- HathiTrust result pages (pre-2023 refresh)
- The Anarchist's Library (theanarchistlibrary.org) —
  closest living approximation
- Project Gutenberg catalog browse pages
- Z-Library's plain-table result view (pre-redesign)
- EB Garamond or Old Standard TT as serif reference (wordmark
  only)
- IBM Plex Mono / JetBrains Mono / Berkeley Mono as
  monospace reference

**Tonal:**

- The Witchfinder General woodcut used in the README — sets
  the name's period weight
- Academic library reading rooms after hours (dim, focused,
  serious)
- Foyle's or Blackwell's antiquarian catalog listings
- The bibliographic blocks in a university-press monograph
  (title page, colophon, copyright page — dense, monospaced,
  informational)

**Anti-references (do not anchor on these):**

- Goodreads, Amazon Books, StoryGraph (consumer book apps)
- Libib, Bookwyrm (personal library / social-book apps)
- JSTOR 2020+, HathiTrust 2023+ (consumer-accessibility
  redesigns)
- Notion, Linear, Raycast (generic productivity — too
  neutral; no bibliographic specificity)
- Kindle / Apple Books / Google Play Books (consumer
  reading apps)
- Any "Netflix for books" product
- Obsidian's default theme (too markdown-editor, not enough
  catalog)

---

## Output target

`SKILL.md` extracted from the claude.ai/design output zip,
dropped at `bookfinder-general/.claude/skills/
bookfinder-aesthetic.md`. All subsequent UI work on
`templates/index.html` (or any future frontend rewrite) routes
through it. The SKILL should be durable enough that a six-
months-later session can reopen Bookfinder cold and produce
consistent output without re-reading this brief.
