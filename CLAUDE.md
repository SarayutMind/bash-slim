## Reading code: always go through bash-slim

To save tokens, read code in this project with the `bash-slim` skill (`.claude/skills/bash-slim/SKILL.md`). Do not open a whole code file with `Read` or `cat` just to understand it.

- Explore a directory: `python .claude/skills/bash-slim/scripts/slim.py <dir>` (outline)
- Find something in a file: `python .claude/skills/bash-slim/scripts/slim.py <file> --outline`, then `Read` only that line range
- Need the whole body: `python .claude/skills/bash-slim/scripts/slim.py <file>`
- Long command output (build, test, install, lint): `<command> 2>&1 | python .claude/skills/bash-slim/scripts/slim.py -`
- `[slim Lx-y]` means lines x to y are hidden. Open them with `Read(offset=x, limit=y-x+1)` only when the answer depends on them.

Use `Read` directly instead when:
- you are about to `Edit` or `Write` those lines (Edit needs the exact bytes, so never copy text from slim output),
- the file is under ~80 lines, or it is JSON, YAML, `.env`, SQL or a migration,
- the user asks to see the exact or full code.
