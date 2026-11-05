## bash-slim: always on

Apply the `bash-slim` skill (`.claude/skills/bash-slim/SKILL.md`) to every task in this project without being asked. Load it at the start of any task that reads code, changes code, or runs commands.

- **Output filtering:** never reprint imports, hooks (`useState`, `useEffect`, ...) or boilerplate in replies. Collapse them with placeholders such as `// ... existing imports/hooks ...`, and show only the core logic, the changed function, or the error lines, with `file:line`.
- **Waiting:** one-line status only (`⏳ build running`, `✅ passed`, `❌ failed: <first error>`). No logs.
- **Token compression when reading:** `python .claude/skills/bash-slim/scripts/slim.py <dir|file> [--outline]`, then `Read` only the lines you need. Logs: `<command> 2>&1 | python .claude/skills/bash-slim/scripts/slim.py -`.
- **Bash:** chain related steps into one call and use quiet flags (`-q`, `--silent`, `| tail -n 5`).
- **Never** put placeholders in `Edit`/`Write` content, files, commits or commands. Those must hold real, complete code, so `Read` the exact lines before `Edit`.
- Show full code only when the user explicitly asks for it, or when a snippet is under ~15 lines.
