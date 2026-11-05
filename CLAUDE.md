## bash-slim: always on

Apply the `bash-slim` skill (`.claude/skills/bash-slim/SKILL.md`) to every task in this project without being asked. Load it at the start of any task that reads code, changes code, or runs commands.

- **Language:** reply in the user's language (Thai prompt → Thai reply). These rules are in English only to keep them short.

- **Output filtering:** never reprint imports, hooks (`useState`, `useEffect`, ...) or boilerplate in replies. Collapse them with placeholders such as `// ... existing imports/hooks ...`, and show only the core logic, the changed function, or the error lines, with `file:line`.
- **Waiting:** one-line status only (`⏳ build running`, `✅ passed`, `❌ failed: <first error>`). No logs.
- **Token compression when reading:** `Grep` to find things. `python .claude/skills/bash-slim/scripts/slim.py <dir>` maps a folder (one line per file); `slim.py <file> --outline` shows one file's structure; then `Read` only the lines you need. Logs: `<command> 2>&1 | python .claude/skills/bash-slim/scripts/slim.py -`.
- **Checks:** lint, typecheck, build and test run through `bash .claude/skills/bash-slim/scripts/check.sh [steps]` (default: fix + typecheck). One short command in, `✅ fix · ✅ typecheck` out, error lines only on failure. If it says `none of your changed files appear in this log`, the errors were already there: say so in one line, don't investigate.
- **Edits:** change files with `Edit`, never with `python - <<'EOF'`, `sed -i` or heredocs in Bash.
- **Bash:** chain related steps into one call; silent on success, full output on failure. Commit: `git -c core.safecrlf=false add -A && out=$(git commit -q -m "..." 2>&1) && git log --oneline -1 || echo "$out"`. Other noisy commands: `out=$(<cmd> 2>&1) && echo "✅ <what> passed" || { echo "❌ <what> failed"; echo "$out" | tail -n 30; }`.
- **Never** put placeholders in `Edit`/`Write` content, files, commits or commands. Those must hold real, complete code, so `Read` the exact lines before `Edit`.
- Show full code only when the user explicitly asks for it, or when a snippet is under ~15 lines.
