#!/usr/bin/env bash
# bookfinder-general — autonomous engineering bot launcher
#
# Usage: bash engineer_command.sh [budget_minutes]
#
# Invoked by GeneralStaff's dispatcher per the engineer_command field
# in GeneralStaff's projects.yaml. Creates a git worktree at
# .bot-worktree on branch bot/work (or $GENERALSTAFF_BOT_BRANCH for
# creative cycles), runs claude -p inside it, exits. Cleanup +
# verification are the dispatcher's responsibility (see GeneralStaff's
# src/cycle.ts). Mirrors the structure of gamr/engineer_command.sh.

set -euo pipefail

BUDGET_MINUTES="${1:-30}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
WORKTREE_DIR="$PROJECT_ROOT/.bot-worktree"
# gs-279: for creative cycles, GeneralStaff sets GENERALSTAFF_BOT_BRANCH
# to the project's creative_work_branch (default "bot/creative-drafts")
# so drafts don't contaminate bot/work's SHA history.
BRANCH="${GENERALSTAFF_BOT_BRANCH:-bot/work}"
CREATIVE_CYCLE="${GENERALSTAFF_CREATIVE_CYCLE:-0}"
DRAFTS_DIR="${GENERALSTAFF_DRAFTS_DIR:-drafts/}"
VOICE_REFS="${GENERALSTAFF_VOICE_REFERENCE_PATHS:-}"

echo "=== bookfinder-general Bot Launcher ==="
echo "Budget: ${BUDGET_MINUTES} min"
echo "Project root: $PROJECT_ROOT"
echo "Worktree: $WORKTREE_DIR"
echo "Branch: $BRANCH"
if [ "$CREATIVE_CYCLE" = "1" ]; then
  echo "Mode: CREATIVE (drafts land in $DRAFTS_DIR)"
fi
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "================================="

# --- Ensure target branch exists (default branch is main on this project) ---
if ! git -C "$PROJECT_ROOT" rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  echo "Creating branch $BRANCH from main..."
  git -C "$PROJECT_ROOT" branch "$BRANCH" main
fi

# --- Create worktree ---
git -C "$PROJECT_ROOT" worktree prune 2>/dev/null || true

if [ -d "$WORKTREE_DIR" ]; then
  echo "Stale worktree found — removing..."
  git -C "$PROJECT_ROOT" worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true
  rm -rf "$WORKTREE_DIR" 2>/dev/null || true
fi

echo "Creating worktree at $WORKTREE_DIR on $BRANCH..."
git -C "$PROJECT_ROOT" worktree add "$WORKTREE_DIR" "$BRANCH"

# --- Install dependencies in worktree ---
echo "Installing dependencies in worktree..."
cd "$WORKTREE_DIR"
# Editable install with test extras. Strict pinning is a CLAUDE.md
# convention; pyproject.toml already pins exact versions via `==`.
pip install -e '.[test]' 2>/dev/null || pip install -e . || true

# --- Build creative-cycle preamble for claude -p prompt (gs-279) ---
# When GeneralStaff signals a creative cycle, splice in a voice-reference
# section ahead of the main brief. Colon-separated paths, one per line.
CREATIVE_PREAMBLE=""
if [ "$CREATIVE_CYCLE" = "1" ]; then
  VOICE_REF_BLOCK=""
  if [ -n "$VOICE_REFS" ]; then
    # Split on ':' portably (works under bash on Windows Git Bash too).
    IFS=':' read -ra VR_ARR <<< "$VOICE_REFS"
    for path in "${VR_ARR[@]}"; do
      [ -n "$path" ] && VOICE_REF_BLOCK="${VOICE_REF_BLOCK}  - ${path}
"
    done
  fi
  if [ -z "$VOICE_REF_BLOCK" ]; then
    VOICE_REF_BLOCK="  (no voice references configured — draft in a neutral technical register)"
  fi
  CREATIVE_PREAMBLE="
## This is a CREATIVE_WORK cycle
You are drafting prose, not writing code that needs to pass tests.
Human review is the gate — you draft, the human edits, the human
publishes. Drafts land in the ${DRAFTS_DIR} directory at the project
root. Do NOT commit to README.md, docs, or any user-facing surface
directly.

## Before drafting — calibrate voice
Read these files first to match the project owner's written voice.
Order matters; read top-to-bottom.

${VOICE_REF_BLOCK}

Match their register, cadence, sentence length, and idiom. Do NOT
write in LLM default voice (no \"unleash\", no \"revolutionize\", no
em-dash-heavy throat-clearing, no engagement-bait verbs).
"
fi

# --- Run autonomous bot ---
echo ""
echo "Launching autonomous claude -p in worktree..."
echo ""

claude -p "You are an autonomous engineering bot working on the bookfinder-general project.

## Your environment
You are in a git worktree on the $BRANCH branch. The main working tree
is on main and may be in use by a human. Do NOT touch the main working
tree — work only in this directory.
${CREATIVE_PREAMBLE}
## Your task
Read state/bookfinder-general/tasks.json and pick the highest-priority
unfinished task (status: 'pending', lowest priority number first; among
same-priority tasks, lowest id first). Work on exactly that task — no
scope creep.

## What you can do
- Add, modify, or delete files at the paths the task explicitly names.
- Add test files that support the claimed work (under tests/).
- Run \`pip install -e .[test]\` if dependencies shift.
- Run \`python -m pytest tests/ -q && python -m ruff check bookfinder_general/ tests/\`
  to verify your changes.
- Commit with a message describing the task you completed.
- Update the task's status to 'done' in state/bookfinder-general/tasks.json
  after committing.

## What you must NOT do
- Modify any file listed in GeneralStaff's projects.yaml hands_off for
  bookfinder-general (CLAUDE.md, README.md, LICENSE, .claude/,
  pyproject.toml, requirements.txt, bookfinder_general/browser.py,
  bookfinder_general/mcp_server.py, bookfinder_general/summarizer.py,
  bookfinder_general/search.py, app.py, main.py, START.bat).
- Bump dependency versions — strict pinning is a CLAUDE.md critical rule.
- Change the Playwright threading model or MCP stdout discipline — those
  are CLAUDE.md critical rules and encoded as hands_off.
- Invent product features or write user-facing copy (unless this is a
  creative cycle, in which case drafts go to ${DRAFTS_DIR} only).
- Pick algorithms — if a task requires an algorithmic decision, abandon
  and write a short note explaining why.

## Verification gate
Tests must pass under
\`python -m pytest tests/ -q && python -m ruff check bookfinder_general/ tests/\`
before commit. If they don't pass, fix or abandon — never commit
failing tests.

## Budget
You have ${BUDGET_MINUTES} minutes total. Stop before the budget runs
out. After committing one task, do NOT pick another in the same
invocation — the dispatcher starts a fresh cycle for the next task.
" \
  --allowedTools "Read,Write,Edit,Bash,Grep,Glob" \
  --dangerously-skip-permissions \
  --mcp-config '{"mcpServers":{}}' \
  --strict-mcp-config \
  --output-format text

echo ""
echo "Bot finished. Exit code: $?"
echo "Ended: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
