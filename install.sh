#!/usr/bin/env bash
# install.sh — install the `birca` skill into a target project.
# Usage:
#   ./install.sh claude-code /path/to/target/project
#   ./install.sh print                      # just print the system prompt to stdout
#   ./install.sh --allow-draft claude-code /path/to/target/project   # override the tag-only guard (loud warning)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALLOW_DRAFT=0
if [[ "${1:-}" == "--allow-draft" ]]; then
  ALLOW_DRAFT=1
  shift
fi

MODE="${1:-print}"
TARGET="${2:-}"

# --- release-policy guard: refuse to install from a moving branch unless explicitly overridden ---
# Uses `git rev-parse --show-toplevel` from HERE itself (not a hard-coded ../.. depth), so this stays
# correct regardless of how many directories deep this script lives inside whatever repo contains it
# (e.g. this monorepo's cpg/products/birca-global-health/universal_skill/, or a future standalone clone).
if REPO_ROOT="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null)"; then
  CURRENT_REF="$(git -C "$REPO_ROOT" describe --tags --exact-match 2>/dev/null || true)"
  if [[ -z "$CURRENT_REF" ]]; then
    CURRENT_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
    echo "WARNING: you are installing from branch '$CURRENT_BRANCH', not a tagged release." >&2
    echo "         This package is DRAFT_NOT_YET_HUMAN_APPROVED until a tagged release exists." >&2
    echo "         Production/public deployment must pin a tag (e.g. birca-v1.0.0)." >&2
    if [[ "$ALLOW_DRAFT" -ne 1 ]]; then
      echo "Refusing to install without --allow-draft. Re-run with --allow-draft for local testing only," >&2
      echo "or 'git checkout <tag>' first for anything beyond your own local testing." >&2
      exit 1
    fi
    echo "--allow-draft set: proceeding anyway. DO NOT use this install beyond local testing." >&2
  fi
else
  echo "NOTE: $HERE is not inside a git checkout — cannot verify tagged-release status." >&2
  echo "      Treat this as an unverified/DRAFT install unless you obtained it from a known-good tag archive." >&2
  if [[ "$ALLOW_DRAFT" -ne 1 ]]; then
    echo "Refusing to install without --allow-draft (no git checkout to verify against)." >&2
    exit 1
  fi
fi

# extract_prompt: pulls the instruction block between explicit markers in SYSTEM_PROMPT.md, not by
# blindly counting ``` fences — robust even if a future edit adds another fenced code example elsewhere
# in the file. Fails loudly (non-zero exit, message on stderr) if the markers are missing/renamed and the
# extraction comes back empty or suspiciously short, instead of silently installing an empty skill.
extract_prompt() {
  local out
  out="$(awk '/<!-- BIRCA_PROMPT_START -->/{f=1; next} /<!-- BIRCA_PROMPT_END -->/{f=0} f && /^```$/{next} f' \
    "$HERE/SYSTEM_PROMPT.md")"
  local line_count
  line_count="$(printf '%s\n' "$out" | wc -l)"
  if [[ -z "$out" || "$line_count" -lt 20 ]]; then
    echo "ERROR: extract_prompt() produced empty or suspiciously short output ($line_count lines)." >&2
    echo "       This usually means the <!-- BIRCA_PROMPT_START/END --> markers in SYSTEM_PROMPT.md" >&2
    echo "       are missing or were renamed. Refusing to install/print an empty or truncated skill." >&2
    return 1
  fi
  printf '%s\n' "$out"
}

# append_claude_pointer: idempotently appends a pointer to /birca in the target project's CLAUDE.md,
# if one exists. Does nothing if CLAUDE.md doesn't exist, or if the pointer is already present.
append_claude_pointer() {
  local claude_md="$TARGET/CLAUDE.md"
  local marker="<!-- birca-skill-pointer -->"
  if [[ -f "$claude_md" ]]; then
    if grep -qF "$marker" "$claude_md" 2>/dev/null; then
      echo "CLAUDE.md pointer already present: $claude_md (not duplicated)"
    else
      {
        echo ""
        echo "$marker"
        echo "## birca skill installed"
        echo ""
        echo "The \`birca\` health-advisory skill is installed at \`.claude/commands/birca.md\`."
        echo "Invoke with \`/birca <health question or context to organize>\`."
        echo "Read \`.claude/commands/birca-disclaimer.md\` before relying on its output."
      } >> "$claude_md"
      echo "Appended a /birca pointer to: $claude_md"
    fi
  else
    echo "No CLAUDE.md found at $TARGET — skipping pointer append (not an error)."
  fi
}

case "$MODE" in
  print)
    extract_prompt
    ;;
  claude-code)
    if [[ -z "$TARGET" ]]; then echo "usage: $0 claude-code <target-project-dir>" >&2; exit 1; fi
    mkdir -p "$TARGET/.claude/commands"
    if ! extract_prompt > "$TARGET/.claude/commands/birca.md"; then
      rm -f "$TARGET/.claude/commands/birca.md"
      exit 1
    fi
    cp "$HERE/LEGAL_DISCLAIMER.md" "$TARGET/.claude/commands/birca-disclaimer.md"
    echo "Installed: $TARGET/.claude/commands/birca.md  (invoke with: /birca)"
    echo "Read before deploying: $TARGET/.claude/commands/birca-disclaimer.md"
    append_claude_pointer
    ;;
  extract)
    if [[ -z "$TARGET" ]]; then echo "usage: $0 extract <output-file>" >&2; exit 1; fi
    if ! extract_prompt > "$TARGET"; then
      rm -f "$TARGET"
      exit 1
    fi
    echo "Wrote extracted birca system prompt to: $TARGET"
    ;;
  *)
    echo "unknown mode '$MODE'. Modes: print | claude-code <dir> | extract <file>" >&2
    echo "For OpenAI / Gemini / generic installs, see INSTALL_OPENAI.md / INSTALL_GENERIC.md (manual paste, no CLI needed)." >&2
    exit 1
    ;;
esac
