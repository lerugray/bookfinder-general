# Bookfinder General — Aesthetic Skill

> For UI work inside the `bookfinder-general/` repo. Route all
> frontend sessions through this document. The design system
> captured here was produced by claude.ai/design on 2026-04-24
> from `claude-design-brief.md`; the canonical reference is the
> full preview at `claude-design-output/Bookfinder General.html`
> (1133 lines, self-contained standalone). If this SKILL and the
> preview disagree, **the preview wins** — update the SKILL to
> match.

**What Bookfinder is:** a research book finder, downloader, and
summarizer. Hunts books on Anna's Archive, extracts text,
auto-translates non-English material, generates stop-slop
summaries + multi-book briefs. Python 3.11+ / Flask web UI /
MCP server / CLI.

**What Bookfinder is not:** a consumer reading app, a personal-
library tracker, a social-book app, a discovery / browsing tool.
It is a **hunting tool.** Users arrive with intent. The UI should
feel like the reference-room computer at a serious research
library, not like a Goodreads clone.

---

## §1 — Core principles (non-negotiable)

| Principle | Rule |
|---|---|
| Register | Archival research terminal, not consumer product |
| Density | Information-dense. Rows, not cards. 15-25 result entries above the fold on 1080p |
| Color | Warm archival dark mode. Parchment text, library-lamp amber, iron-oxide error, manuscript green success. **No cyan.** |
| Typography | Three faces, three jobs: serif (wordmark + blockquotes only), sans (UI chrome), monospace (catalog data) |
| Motion | Essentially none. No hover-scale, no fade-in, no spinner swoops |
| Corners | 0px radius. Square panels, square buttons, square inputs |
| Shadows | None. Flat. A research terminal does not render material depth |
| Whitespace | Structural, not aesthetic. A 16px gap exists because a section ended |
| Emoji | None. Ever. No magnifier, no book, no witch, no sparkles |

**Grep-for-violations patterns** (Claude Code should catch these):
- `border-radius: 8px`, `border-radius: 10px`, `border-radius: 12px` (consumer-app softness)
- `box-shadow: 0 .*px .*px rgba(0,0,0` (material depth)
- `linear-gradient(` on backgrounds or buttons (brand-gradient leakage)
- `#00d4ff`, `#22d3ee`, `cyan`, `#00ffff` — cyan in any accent role
- `spinner`, `spin`, `rotate(360deg)` — generic SaaS spinners
- `animation: .* ease`, `transition: .* ease` — non-linear easing
- `🔍`, `📚`, `🧙`, `✨`, `🎉` — any emoji in UI copy or templates
- `Welcome back`, `Welcome to Bookfinder`, `Congratulations` — consumer-app onboarding register
- `max-width: 1000px`, `max-width: 1200px` — marketing-page content caps (the UI uses 1400-1600px)

---

## §2 — Palette (locked)

Every color has a semantic role. Do not substitute. Use the CSS
custom properties from `claude-design-output/Bookfinder General.html`
verbatim.

### Dark mode (primary — researchers work at night)

```css
--bg:        #0f0e0c;   /* warm near-black reading room */
--panel:     #141310;   /* panel inset, barely visible */
--panel-2:   #181712;   /* second-level panel (detail expansion) */
--rule:      #2a2722;   /* hairline horizontal / vertical rule */
--rule-hi:   #3a362d;   /* hairline on hover, toggle box edge */
--text:      #ece6d3;   /* parchment — primary text */
--text-dim:  #8a8474;   /* aged-paper — secondary text, labels */
--text-vvdim:#5a554a;   /* deep dim — tertiary, timings, sep chars */
--amber:     #c8a25a;   /* library-lamp gold — PRIMARY ACCENT */
--amber-dim: #8a6f3c;   /* amber dimmed — borders, hover echo */
--iron:      #a04848;   /* iron-oxide — errors, destructive action */
--green:     #789a5a;   /* manuscript green — success, in-library */
```

### Light mode (secondary — law-library reading room)

Activated via `html[data-theme="light"]`. Available but NOT the
product default. Researchers use this at night; light mode is
a concession, not the register.

```css
--bg:#f4f0e4;  --panel:#ebe6d6;  --panel-2:#e2dcc8;
--rule:#d4cdb6; --rule-hi:#b8ae93;
--text:#2a2620; --text-dim:#6b6655; --text-vvdim:#9a9484;
--amber:#8a6a2a; --amber-dim:#6b521d;
--iron:#7e3434; --green:#556b36;
```

### Accent variants (optional, per-deploy preference)

`html[data-accent="sepia"]` and `html[data-accent="green"]`
offered as an operator preference — same structural role, shifted
hue. Amber is default and the brand. Do not expose a color-picker
UI; this is an operator preference, not a user-customization theme.

### Usage rules

- **Amber** for: search-bar focus border, active tab, link hover,
  result-count numerals, top-rank marker, `::selection`,
  amber-on-copy flash, primary-action button fill on hover,
  download-link hover, library filter focus
- **Iron** for: error states, destructive actions
  (Remove-from-library), failure badges
- **Green** for: `key: set` status, in-library badge, translated
  badge, any "already complete" semantic
- **`::selection`** uses amber background + bg foreground
  (inverted). Small detail that reads as archival terminal.

### Forbidden

- Cyan / electric blue / `#00d4ff`-family (generic SaaS)
- Pure white `#ffffff` (too clinical; use `--text` parchment)
- Pure black `#000000` (never; always warm `--bg`)
- Rainbow category palettes in any chart / status indicator
- Gradients of any kind on backgrounds, buttons, or borders
- Neon / saturated electric colors
- Bootstrap / Tailwind default color tokens

---

## §3 — Typography (three faces, three jobs)

Loaded via Google Fonts in the preview; equivalent to system
fallbacks for offline development.

```css
--font-serif: 'EB Garamond', 'Old Standard TT', Georgia, serif;
--font-sans:  'IBM Plex Sans', system-ui, -apple-system, Segoe UI, sans-serif;
--font-mono:  'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace;
```

### Job assignments (STRICT)

| Face | Used for |
|---|---|
| Serif (EB Garamond) | Wordmark ("Bookfinder General"), tagline italic, help-modal heading + sub, brief-topic title, body dropcap first letter (detail-body), blockquotes in rendered Markdown |
| Sans (IBM Plex Sans) | Result titles, library titles, book-detail body prose, filter input text, abstract text |
| Monospace (IBM Plex Mono) | All catalog data: rank numbers, MD5 hashes, filesize, year, language codes, library IDs, field labels (uppercase small-cap tracked), button copy in action buttons, nav-button counts, status-strip text, search-prompt `>` glyph, library-filter `/` glyph, keyboard shortcut labels in help modal, timing strings ("search: 2.34s"), detail-tab labels, detail-tab pills |

**Violations to catch:**
- Serif used on a result row title → wrong register
- Serif used on a filter label → wrong register
- Monospace used on the wordmark → wrong register
- Three different sans faces — reduce to one
- Fourth face added (display, script, etc.) — reject; three is the limit

### Weight discipline

Per face, two weights max:

- Serif: 400 Regular (body/dropcap/blockquote), 500 Medium (wordmark). Italics permitted for tagline + blockquote + foreign-language titles.
- Sans: 400 Regular (body), 500 Medium (result/library titles, dropdowns), 600 Semibold (detail h1/h2/h3).
- Monospace: 400 Regular is standard. Use 500/600 only for field-label emphasis.

**Forbidden:**
- Extralight 200, hairline 100 (any face)
- Black 900 or Heavy 800 (any face)
- Italic on sans or monospace (only serif gets italic)

### Size discipline

Dense. Researchers read catalog data at 10-13px all day.

| Role | Size |
|---|---|
| Wordmark | 30px |
| Brief-topic title | 24px |
| Detail h1 | 20px |
| Help-modal heading | 20px |
| Abstract / detail body | 13-15px |
| Result / library titles | 14px |
| Result meta (mono) | 11px |
| Search input | 15px |
| Result byline | 12px |
| Field labels (mono, uppercase) | 10px |
| Metablock dt (uppercase) | 10px |
| Badges (mono, lowercase) | 10px |
| Rank numerals | 11px |
| Keyboard `<kbd>` | 11px |

**Letter-spacing conventions:**

- Field labels + section labels (monospace, uppercase): `0.15em`
- Detail-tab labels, nav-btn labels (uppercase mono): `0.12em`
- Action-button labels: `0.08em`
- Result meta: `0.02em` (tight — reads as data)
- Body prose: default (0)

---

## §4 — Density + layout

### Padding increments (dense → comfortable toggle)

Default `html[data-density="dense"]`:

```css
--row-pad-y: 8px;
--row-pad-x: 12px;
```

Optional `html[data-density="comfortable"]`:

```css
--row-pad-y: 12px;
--row-pad-x: 16px;
```

Vertical structural spacing beyond rows: 4 / 6 / 8 / 12 / 16 / 20 / 24 / 28 px. Do NOT use 32 / 40 / 48 / 64 — those are marketing-page rhythms.

### Content width

- **Main content area:** `max-width: 1600px`, `padding: 24px 28px 72px`. Catalog UIs use width; they don't cap at 1000-1200px the way marketing pages do.
- **Rendered Markdown bodies** (book detail, brief body): `max-width: 780px` — long-form prose needs readable measure.
- **Abstract text** (expanded result): `max-width: 80ch`.
- **Metablock** (expanded result field-label grid): `max-width: 760px`.
- **Help modal:** `max-width: 560px`, `width: 90%`.

### Grid patterns

- **Result row:** `grid-template-columns: 28px 1fr auto auto;` (rank / main-column / meta / actions)
- **Library row:** `grid-template-columns: 1fr auto auto auto;` (main / badges / meta / lib-id)
- **Metablock:** `grid-template-columns: 90px 1fr;` (dt / dd)
- **Detail layout:** `grid-template-columns: 240px 1fr;` (sticky sidebar / body)
- **Top bar:** `grid-template-columns: auto 1fr auto;` (wordmark / library-path / nav)

### Borders

- Between result entries: `border-bottom: 1px solid var(--rule);` Replaces rounded-card separators.
- Selection left-rule: `border-left: 2px solid var(--amber);` with `padding-left: calc(var(--row-pad-x) - 2px)` to prevent content shift. (Selected-row signature — elegant; preserve.)
- Search bar: `border: 1px solid var(--rule); border-bottom-width: 2px;` — the 2px-bottom asymmetry is the "input-is-active-surface" cue, replaces box-shadow focus ring.
- Focus state: border-color flips to `--amber`. No outline ring, no box-shadow glow.

### Skip-layers

- No box-shadow anywhere (`box-shadow: none` equivalent across all elements)
- No border-radius anywhere (or 0-2px max if somewhere must)
- No backdrop-filter / blur
- No glass-morphism panels

---

## §5 — Component vocabulary (named patterns)

These are the patterns future sessions reach for. All defined in
`claude-design-output/Bookfinder General.html`. Names below match
the preview's CSS class names.

### 5.1 `topbar`
Wordmark + tagline (left), library path (center-right, monospace,
small), nav buttons (right). `grid-template-columns: auto 1fr auto`.
The library path is `~/Research/BookFinder · 47 volumes` — monospace
with the numeric count in `--amber`.

### 5.2 `wordmark` + `tagline`
The ONE place serif lives by default. *"Bookfinder General"* in EB
Garamond 500, 30px. *"Hunts books, not witches."* tagline directly
under, italic EB Garamond 13px, `--text-dim`. Do not remove the
tagline. Do not replace the serif here with sans (a prior session
made that substitution and erased the product's voice).

### 5.3 `search-bar`
Wide input with `>` shell-prompt glyph (monospace, amber) as a
leading visual cue. Inline `Search` submit button on the right,
separated by a 1px rule. Focus state flips border to amber. No
icon search-magnifier; `>` is the tell.

### 5.4 `field` + `field-label`
Compact `<select>` or `<input>` with an **uppercase monospace
label above** the control (not beside it). Label is 10px,
letter-spacing 0.15em, `--text-dim`.

### 5.5 `advanced-toggle` + `advanced-row`
Disclosure control. Opens a 1px-bordered panel row with year-range
(two-input with an arrow between), max-size input, and toggles
(Prefer EPUB, Skip scans over max size). Labeled `+ advanced` (not
"Show advanced options" — keep it terse and monospace).

### 5.6 `results-meta`
Header line above the results list. Result count left (amber numeral),
"re-ranked by title-word overlap" secondary-text right of it, timing
("search: 2.34s · annas-archive.gl") far right in `--text-vvdim`.
Monospace, 11px, uppercase, 0.12em tracked.

### 5.7 `result-row`
The product's core unit. Grid: `28px | 1fr | auto | auto` (rank /
main / meta / actions). `result-actions` has `opacity: 0` by default
and becomes `opacity: 1` on `:hover`, `.selected`, or `.expanded`.
Selected state adds left-rule amber stripe.

Components inside:
- `rank` — right-aligned monospace, `--text-vvdim`. Top-3 results
  get `rank.top` with `--amber` color. Never flashy.
- `result-main > result-title` — sans 14px medium. `.foreign`
  class italicizes non-English titles per academic convention.
- `result-main > result-byline` — sans 12px `--text-dim`.
- `result-meta` — monospace 11px, tab-separated by thin `|` char
  or ` · ` middle dot in `--text-vvdim`. `.fmt` highlights the
  extension (EPUB / PDF) in `--text`.
- `result-actions > act` — monospace, uppercase, 11px, 0.08em
  tracked. `act.primary` is amber-bordered (Download). `act.in-library`
  is green (already downloaded). Hover: text + border flips to amber.

### 5.8 `expand` + `metablock`
Inline expansion under a result row. Padded 14/12/20/46 (the 46 is
visual indent matching the rank column). Inside:

- **Metablock** — dl/dt/dd grid with `grid-template-columns: 90px 1fr`.
  dt is uppercase small-cap monospace 10px, 0.15em tracked. dd is
  monospace. `dd.hash` (MD5) is amber, `user-select: all; cursor: copy`
  — click-to-copy with `.copied` flash class.
- **Abstract** — sans 13px max-width 80ch, with a 1px left-rule in
  `--rule` and a small uppercase mono "ABSTRACT" label above.
- **Download-links** — labeled "DOWNLOAD LINKS" uppercase mono.
  Each link: source chip (`--text-vvdim`, 80px fixed width) +
  monospace link text. Hover turns amber.
- **Action-bar** — divided from content above by a 1px rule. Action
  buttons use the `act` monospace-uppercase convention.

### 5.9 `status-strip`
Fixed-bottom persistent strip. `position: fixed; bottom: 0; left: 0;
right: 0;` Monospace 11px, `--text-dim`. Contents (right-aligned):

- `mirror: annas-archive.gl` (amber for the host value)
- `last: 2.34s` (white for value)
- `key: set` (green for set, iron for none)
- `sync: off` (iron/warn)
- `press ? for keys` hint (vvdim with amber `?`)

Left side when active: italic `--text-vvdim` status text (e.g., "idle",
"searching annas-archive.gl via playwright..."). `pointer-events: none`
so it doesn't intercept clicks on content below.

### 5.10 `library-row`
Similar layout to result-row but different column priorities.
Grid: `1fr | auto | auto | auto` (main / badges / meta / lib-id).

- **`badges`** — small uppercase monospace 10px, bordered. Three
  types: `badge.text` (white, file extracted), `badge.translated`
  (green, translation complete), `badge.summarized` (amber, summary
  generated). A book with all three shows `[text · translated · summarized]`.
- **`lib-id`** — truncated MD5 in monospace `--text-vvdim`, `cursor: copy`.
  Hover → amber. `.copied` state flashes amber.

### 5.11 `detail` layout (book-detail screen)
Two-column: `240px sticky sidebar | 1fr body`.

- Sidebar: back link ("← Library" uppercase mono), dense metablock
  (dt 60px width, smaller 9px uppercase), action column (stacked
  `act` buttons, text-align left). Destructive action ("Remove from
  library") is iron-colored.
- Body: top tab bar (Original / Translated / Summary) with language
  pills beside each label (monospace 10px). Tabs: `detail-tab.active`
  gets amber color + amber border-bottom (2px).
- Content: long-form rendered Markdown. See §5.12.

### 5.12 `detail-body` (rendered Markdown)
Long-form content renderer for book excerpts, translations,
summaries, briefs.

- Max-width 780px, 14px body, line-height 1.65.
- `h1` — sans 600, 20px, `--text`, no top margin (first-in-column).
- `h2` — sans 600, 16px, `--text`.
- `h3` — sans 600, 14px, `--text-dim`, uppercase, 0.08em tracked.
- `p` — sans, 0.8em margins.
- `.dropcap::first-letter` — serif, 2.6em, floated left,
  `--amber`. Applied on first paragraph of a body. Per brief:
  "serif is NOT allowed in rendered book content" — the dropcap
  is the **one** exception (decorative first-letter). The rest
  of body prose stays sans.
- `blockquote` — serif italic `--text-dim` with 1px left rule in
  `--amber-dim`. Second exception for serif.
- `hr` — `border-top: 1px solid var(--rule);` with 2em margin.

### 5.13 `brief-header` + `brief-chip`
Research brief screen header:

- `brief-topic-label` — monospace uppercase 10px, 0.15em
- `brief-topic` — serif 24px, `--text` (the only other serif
  heading location besides wordmark — used because it names
  the research topic, which is content, not UI chrome)
- `brief-chip` — bordered monospace tag. MD5 id in amber, title
  text in `--text`, `×` remove button in dim. `.add` variant is
  dashed-border + dim text + `+ add book` copy.

### 5.14 `help-modal`
Keyboard shortcut reference. Triggered by `?`.

- Overlay: `rgba(15,14,12,0.88)` — warm dark, matches bg
- Body: 560px max, 28/32 padding
- Heading "Keymap" (serif 20px 500)
- Sub: "Bookfinder rewards speed." (serif italic dim)
- Grid: `auto | 1fr`, `<kbd>` cells are amber in a 1px `--rule`
  border box, min-width 30px, text-align center
- Close hint: "press esc or ? to dismiss" (10px dim uppercase
  0.15em tracked)

### 5.15 `cursor-blink` helper
`::after { content: "_"; color: var(--amber); animation: blink 1s
steps(2) infinite; }`. Used where monospace-prompt expects an input
cursor. Two-step (not smooth) animation — wrong kind of computer
smooths cursors.

### 5.16 `copy-flash` pattern (instead of toast)
`transition: background 100ms linear, color 100ms linear;`
Apply `.flash` class for 100ms → the element paints amber-bg /
bg-fg as confirmation. No toast, no pop-up, no notification bar.
Research terminal: you clicked; it flashed; you know.

---

## §6 — Interaction patterns

### Keyboard shortcuts (canonical — do NOT reassign)

| Key | Action |
|---|---|
| `/` | Focus search input |
| `Esc` | Clear focus / close panels / close help modal |
| `Enter` | Submit search / open selected result |
| `j` | Next result in list |
| `k` | Previous result in list |
| `o` | Expand (open) selected result inline |
| `d` | Download selected to library |
| `l` | Jump to library screen |
| `s` | Jump to search screen |
| `b` | Jump to briefs screen |
| `?` | Open keymap modal |

Any new screen or action adds a letter to this list — do not
re-purpose any existing key. The keymap modal (`?`) is the
discoverability surface; users trained in vim/less will notice
j/k immediately. Future sessions extending the UI must preserve
these bindings.

### Click-to-copy affordances

Every MD5, library ID, path, hash, and metadata identifier is
click-to-copy. No "Copied!" toast. Instead: `.copy-flash` (§5.16).

### Action feedback

- Hover on `.act` buttons → text + border flip to amber
- `.act.primary` hover → filled amber background, bg-color text
- Selected result → `--panel-2` background + amber left-rule
- Expanded result → `.expand` section appears below; its close
  is the same key (`o`) or clicking the rank

### No modal confirmations

Downloads begin on click. Deletions show iron-color, but no
"Are you sure?" — researchers don't need hand-holding, and
mistakes are undo-able via library.

### Motion constraints

- `transition: opacity 100ms linear` on result-actions reveal
- `transition: background 100ms linear, color 100ms linear` on
  copy-flash
- `@keyframes blink { 50% { opacity: 0; } }` with `steps(2)` on
  cursor-blink
- **Nothing else.** No fade-in on page load, no slide-in on panel
  open, no scroll-triggered reveal. If motion is added, it must
  be linear, ≤150ms, and serve an information-architecture purpose
  (not decoration).

---

## §7 — URL/routing + state

The preview implements screen-switching via `data-screen` attribute
on nav buttons + matching `.screen` sections. Production Flask
implementation should:

- **Deep-link every screen** — `/search?q=…&lang=de&ext=epub`,
  `/library?sort=added&filter=…`, `/book/<md5>`,
  `/brief/<brief-id>`
- **URL-param-persistent filters** — a search with
  `?lang=de&ext=epub` survives a page refresh
- **Back/forward browser nav** must work — the preview's
  `data-screen` switcher is a simplification; real routing
  is needed in prod

---

## §8 — Screens (per-screen structural templates)

See the preview file for full markup. Brief structural checklist
per screen:

### Search screen
Search bar → filter row → advanced (collapsed) → results-meta →
results list → empty state (if no results).

### Library screen
Lib-controls (filter + sort-group) → lib-count strip → library-list
(library rows). The lib-filter uses a `<span class="slash">/</span>`
as a keyboard-shortcut hint glyph inside the input's left area.

### Book detail screen
Two-column `detail` layout. Sidebar sticky with metablock + actions.
Body has tab-switchable content (Original / Translated / Summary).
First paragraph of body gets `.dropcap` class.

### Research brief screen
Brief header (topic label + topic serif title + source chips).
Action row (Regenerate / Export PDF / Export Markdown) + generation
metadata on right. Body is rendered Markdown like book-detail body.

### Help modal
Overlays any screen. Keymap grid. Esc or `?` to dismiss.

### Status strip
Present on all screens (position: fixed bottom).

---

## §9 — Failure modes the SKILL must catch

These are the patterns future sessions will default toward if
unchecked. Catch proactively.

### 9.1 Consumer-app drift

| Drift | Fix |
|---|---|
| "Welcome back!" / "Welcome to Bookfinder!" greeting | Delete. Researchers do not need greeting |
| Rounded cards with 10-12px radius on result rows | Replace with hair-rule row separators |
| Hero illustration on empty states | Replace with one line of monospace italic text |
| "Oops!" / emoji-heavy error messages | Replace with dry technical text |
| Toast notifications on copy | Replace with `.copy-flash` pattern (§5.16) |
| "Are you sure?" modal on delete | Remove; just perform the action (reversible) |
| Spinner rings on search-in-progress | Replace with `cursor-blink` in status-strip-left text |
| Marketing-page max-width (1000-1200px) | Raise to 1400-1600px for catalog surfaces |
| Star ratings, thumb-up/down on results | Remove entirely — Bookfinder is not a rating system |
| "Trending searches" / "Popular this week" | Out of scope; not that kind of product |

### 9.2 Register violations

| Violation | Fix |
|---|---|
| Emoji in button copy (🔍, 📥, ⬇️) | Remove emoji; use monospace uppercase text labels |
| Sans font on the wordmark | Revert to EB Garamond 500 |
| Cyan accent creeping back (`#00d4ff`, `cyan`, `#22d3ee`) | Revert to `--amber` (#c8a25a) |
| Bright green success (`#22c55e`, `#10b981`) | Revert to `--green` (#789a5a, manuscript green) |
| Bright red error (`#ef4444`, `#ff6b6b`) | Revert to `--iron` (#a04848, iron-oxide) |
| Friendly placeholder text ("Search for anything!") | Tighten to dry directive ("Title, author, ISBN, or topic.") |
| "Drag and drop files here" / "Click or drop" consumer UX | Bookfinder hunts books remotely; no drop-zone pattern |
| Chat-bubble friendliness in empty states | Replace with single-line italic hint |

### 9.3 Structural violations

| Violation | Fix |
|---|---|
| Card grid of results (3-column, boxed, rounded) | Revert to result-row table pattern |
| Missing the tagline under wordmark | Re-add "Hunts books, not witches." italic serif |
| Missing the library-path indicator in topbar | Re-add — it's the operator's "you are here" |
| Missing the status strip | Re-add — bottom-right persistent operator info |
| Hiding the keymap modal / removing `?` shortcut | Restore; keyboard navigation is core UX |
| Adding a "Filter library…" wordy placeholder | Replace with `/` glyph + terse placeholder |

### 9.4 Load-bearing copy (do not alter)

- Wordmark: **Bookfinder General**
- Tagline: **Hunts books, not witches.**
- Search placeholder: **Title, author, ISBN, or topic.**
- Empty-state: **No results. Try the author's surname plus one keyword from the title.**
- Help-modal heading: **Keymap**
- Help-modal sub: **Bookfinder rewards speed.**
- Library empty: **Library empty. Search and download to begin.**

A future session rewriting copy for "tone consistency" or "better
UX" will want to flatten these into generic SaaS neutrals. Reject.

---

## §10 — Reference files

When in doubt, open these and match:

- `claude-design-output/Bookfinder General.html` — full standalone
  preview with inline CSS and mock data. Open in a browser to see
  the design system live. **This is the source of truth** — if
  this SKILL and the preview disagree, the preview wins. Update
  the SKILL to match.
- `claude-design-output/app.js` — interactive behaviors (search
  state, library state, result rendering logic). Reference
  patterns for Flask integration.
- `claude-design-output/tweaks-panel.jsx` — the tweakable
  operator preferences (density / accent / theme / show-rank /
  show-status-strip). Flask deploy can keep or remove; not
  user-facing required.
- `claude-design-brief.md` (at repo root) — the original brief.
  Captures the *why* behind the aesthetic decisions.
- `templates/index.html` — current Flask template (generic
  dark-cyan, pre-redesign). The target-of-refit for the first
  integration session.

---

## §11 — Integration notes

The preview is self-contained HTML (vanilla CSS + vanilla JS +
React-in-script-tag for the tweaks panel). It is **not** a Flask
template. First integration session needs to:

1. Extract CSS into `templates/` + a proper `static/css/` file
   (or inline if Flask's Jinja2 rendering prefers).
2. Port the component markup into Jinja2 templates, swapping
   the mock-data loops in `app.js` for `{% for %}` blocks fed
   by the Flask view.
3. Drop the tweaks-panel React dependency unless Ray wants
   operator preferences surfaced (likely: no for v1; keep
   `data-density="dense"` hardcoded and add later).
4. Wire keyboard shortcuts (§6) as a small JS module. All 11
   bindings must land in v1.
5. Preserve every CSS custom property name from §2 — future
   sessions will look for `--amber`, `--text-dim`, etc.

The existing `templates/index.html` (the generic dark-cyan
original) is the target being replaced. Don't try to "tweak"
it into compliance — the visual system is different enough
that a port is cleaner than a refit.

---

## §12 — Voice

Bookfinder's UI copy is **terse, direct, archival.** No
enthusiasm, no urgency, no friendly onboarding voice.

Tonally on-register:
- *"No results. Try the author's surname plus one keyword from the title."*
- *"Library empty. Search and download to begin."*
- *"Bookfinder rewards speed."*
- *"Mirror: annas-archive.gl · last: 2.34s · key: set · sync: off"*

Tonally off-register (reject):
- *"Oh no! No books found. Try a different search?"*
- *"Your library is empty — let's find your first book! 📚"*
- *"Hit the ground running! These shortcuts will save you time."*
- *"Last search took 2.3 seconds 🚀"*

When writing new copy, pretend the reader is a librarian who
has been at this for 30 years, not a first-time app user who
needs encouragement. That reader is actually the target user.
