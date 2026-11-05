---
name: bash-slim
description: Token compression and output filtering for every task in this project. Use whenever you read code with Read or Bash, show code to the user, report command results, or wait on a long-running command. Collapses imports, hooks (useState, useEffect, ...) and boilerplate into placeholders such as `// ... existing imports/hooks ...`, shows only core logic, the changed function or the failing lines, and keeps waiting/status updates to a single line.
---

# bash-slim

Goal: spend fewer tokens on what you read and on what you write, and answer faster. Target: over 75% less output than printing whole files or whole logs.

**Reply in the user's language.** A Thai prompt gets a Thai reply. This file is in English only to keep it short.

## Strict rules for output

1. **Never reprint long code in full.** In replies to the user, do not print imports, hooks (`useState`, `useEffect`, `useRef`, `useMemo`, `useCallback`, custom `use*`) or boilerplate (providers and wrappers, prop/type declarations nobody changed, styles, config objects, repeated JSX/template markup).
2. **Collapse them with a placeholder right away**, in the comment syntax of the file:

   | Language | Placeholder |
   |---|---|
   | TS / JS | `// ... existing imports/hooks ...` · `// ... existing imports ...` · `// ... existing hooks ...` · `// ... unchanged: handleReset, handleClose ...` |
   | JSX | `{/* ... existing JSX ... */}` |
   | Vue / HTML | `<!-- ... existing template ... -->` |
   | CSS / SCSS | `/* ... existing styles ... */` |
   | Python | `# ... existing imports ...` |

3. **Print only what matters:** the core logic, the function or block you changed, or the exact lines where the error happens. Put `file:line` above the snippet and keep at most 1–2 lines of context around the change.
4. **While loading or waiting**, give a one-line status and nothing else, e.g. `⏳ build running (~2 min)`, then `✅ build passed` or `❌ build failed: <first error line>`. Never paste the full log.

### Example

Wasteful:

```tsx
import React, { useState, useEffect } from "react";
import { Box, Button, TextField } from "@mui/material";
import { api } from "@/lib/api";
// ...20 more lines of imports and hooks...
const handleSubmit = async () => {
  if (total < 0) return setError("ห้ามติดลบ");
  await api.save(form);
};
// ...80 lines of JSX...
```

bash-slim (`src/features/school/school-form.tsx:42`):

```tsx
// ... existing imports/hooks ...
const handleSubmit = async () => {
  if (total < 0) return setError("ห้ามติดลบ"); // new
  await api.save(form);
};
// ... existing JSX ...
```

## Where placeholders are not allowed

These rules apply only to text shown to the user. The following must always contain real, complete content:

- `Edit` `old_string` / `new_string`, `Write` content, and anything else saved to disk. A placeholder written into a file breaks the code.
- Commit messages, patches, and shell commands.
- Code the user explicitly asks to see in full. Show it in full.
- Snippets under ~15 lines. Collapsing them saves nothing, so show them as they are.

## Token compression when reading (Read / Bash)

Filter before the text reaches the context. Telling yourself to "ignore the imports" after a full `Read` saves nothing.

| Need | Command (from the project root) |
|---|---|
| Find where something is (a route, an API call, a function) | `Grep` first. It is the cheapest search. |
| Map a directory | `python .claude/skills/bash-slim/scripts/slim.py <dir>` (one line per file: `path (lines)  line name · line name`) |
| Find a function or component | `python .claude/skills/bash-slim/scripts/slim.py <file> --outline`, then `Read(offset, limit)` on that range only |
| Read a whole file | `python .claude/skills/bash-slim/scripts/slim.py <file>` (imports, hook runs, long comments, `<style>` and repeated lines collapsed to `[slim Lx-y]`) |
| Long command output | `<command> 2>&1 \| python .claude/skills/bash-slim/scripts/slim.py -` or `\| tail -n 20` |

- `[slim L12-30]` means lines 12 to 30 are hidden. Open them with `Read(offset=12, limit=19)` only if the answer depends on them.
- Before `Edit`, `Read` the exact lines you will change.
- Use `Read` directly for files under ~80 lines, and for JSON, YAML, `.env`, SQL and migrations.
- Never run `slim.py <dir> --outline` or `--full` on a whole directory. Map it, then outline only the files you need.
- Run `python .claude/skills/bash-slim/scripts/slim.py --help` for the other flags (`--keep`, `--stats`, `--numbers`, `--full`).

## Bash calls: short command in, one line out

The user sees every Bash call as a box with the command (IN) and its output (OUT). Keep both short.

### Lint / typecheck / build / test: use `check.sh`

```bash
bash .claude/skills/bash-slim/scripts/check.sh              # fix + typecheck → "✅ fix · ✅ typecheck (41s)"
bash .claude/skills/bash-slim/scripts/check.sh typecheck build test        # package.json scripts by name
bash .claude/skills/bash-slim/scripts/check.sh fix 'api=yarn workspace @repo/api typecheck'   # name=command
```

- `fix` runs biome (or prettier / eslint) with `--write` on changed files only, like lint-staged.
- On failure it prints the error lines with `file:line` (many biome diagnostics are grouped by rule), the tool's summary (`Found 441 errors`), whether your changed files appear in the log, and the path of the full log.
- Trust those lines. When they say `none of your changed files appear in this log`, the errors were already there: report that in one line and move on. Do not run extra commands to investigate them.
- Run it from the project root. Do not write your own `| tail`, `| grep` or `2>&1` chains for these checks.

### Edit files with `Edit`, not scripts

Never change source files with `python - <<'EOF'`, `sed -i`, `perl -pi` or `cat > file <<EOF` inside Bash. The whole script lands in IN. `Edit` shows only the changed lines as a diff.

### Other commands: silent on success, full output on failure

`-q` alone is not enough. CRLF warnings come from `git add`, and pre-commit hooks (husky, lint-staged, biome) print their own log no matter what flags `git commit` gets. Capture the output and print it only when the command fails:

```bash
# commit (+ push): prints one line, e.g. "331555b [FIX] Page size 100", or the full log if a hook fails
git -c core.safecrlf=false add -A \
  && out=$(git commit -q -m "..." 2>&1) && git log --oneline -1 || echo "$out"
git push -q

# any noisy command (build, test, install, migrate)
out=$(yarn build 2>&1) && echo "✅ build passed" || { echo "❌ build failed"; echo "$out" | tail -n 30; }
```

- Chain related steps into one Bash call. Fewer calls mean fewer `Bash(...)` lines on screen.
- Other quiet flags: `npm ci --silent`, `yarn --silent`, `git pull -q`, `git checkout -q`, `git merge -q`.
- Never drop the failure output. When a command fails, the log is what the user needs.
- Keep the description short, e.g. `Commit + push to dev`, `Lint + typecheck`.

## Input / Workflow / Output

- **Input:** any task in this project that reads code or logs, changes code, or runs commands.
- **Workflow:**
  1. Read compressed: outline first, then only the lines you need.
  2. Do the work. Edits use real, complete code.
  3. Reply filtered: changed part plus placeholders, error lines, or a one-line status.
- **Output:** a short reply with `file:line`, only the changed or failing code, and placeholders for everything else.
