---
name: bash-slim
description: Token-saving way to read code. Use whenever you explore or read source files to understand them rather than to edit them right away, such as mapping a directory, finding where something lives, reviewing or explaining a file, or reading any code file over ~80 lines. Prints an outline, or a slim view where imports, runs of useState/useRef-style hook declarations, long comments, Vue/Svelte <style> blocks, near-duplicate lines and very long lines are collapsed into `[slim Lx-y]` placeholders. Also collapses repeated lines in long command output piped through it.
---

# bash-slim

Read less first, then read exactly what you need. `scripts/slim.py` collapses boilerplate **before** it reaches the context. Telling yourself to "ignore imports" after a `Read` saves nothing, because the full file is already in the context by then.

## Input

| What you have | Command (run from the project root) |
|---|---|
| A directory | `python .claude/skills/bash-slim/scripts/slim.py <dir>` (outline of every code file) |
| One file, you need its shape | `python .claude/skills/bash-slim/scripts/slim.py <file> --outline` |
| One file, you need its body | `python .claude/skills/bash-slim/scripts/slim.py <file>` |
| Long command output | `<command> 2>&1 \| python .claude/skills/bash-slim/scripts/slim.py -` |

Use `python3` where `python` is not on PATH. Files of these types get the code rules: `.ts .tsx .js .jsx .mjs .cjs .vue .svelte .py`. Every other file gets only the `similar` and `long` rules.

| Flag | Effect |
|---|---|
| `--outline` | Signatures only: functions, components, classes, types, routes, `<template>/<script>/<style>`, with line numbers. Default for directories. |
| `--full` | Slim view instead of outline for a directory. |
| `--numbers` | Add line numbers to kept lines in the slim view. Costs about 5 chars per line, so use it only when you need many line references. |
| `--keep imports,hooks,comments,style,similar,long` | Switch rules off, e.g. `--keep imports` when debugging an import. |
| `--stats` | Print only the size before and after. |
| `--lang js\|vue\|py\|text` | Force the language (for stdin or unknown extensions). |
| `--min-run N` | Minimum hook declarations in a row before collapsing (default 3). |
| `--max-files N` | Cap on files per directory (default 60). |

Directory walks skip `node_modules`, `.git`, `.next`, `dist`, `build`, `coverage`, other hidden folders, `*.min.js`, `*.d.ts`, maps and lockfiles.

## Workflow

1. **Map.** Run the script on the directory. Pick the files that matter from the outline.
2. **Locate.** Run `--outline` on a file to find the function or component you need. Outline rows carry line numbers.
3. **Read exactly.** Open only that range with `Read(file, offset=<start>, limit=<count>)`, or run the slim view when you need the whole body.
4. **Expand on demand.** A placeholder `[slim L12-30]` means lines 12 to 30 are hidden. Open them with `Read(offset=12, limit=19)` or `sed -n '12,30p' <file>` only if the answer depends on them.
5. **Before editing**, `Read` the exact lines you will change. `Edit` needs the real bytes; slim output is not the file.
6. **Command output.** Pipe build, test, install and lint output through `slim.py -` when it may be long or repetitive.

## Output

Each file starts with a header that shows the saving:

```
=== src/app/page.tsx  42→25 lines, 1.0k→0.7k chars (-32%) ===
"use client";
[slim L2-6] comment(5): Page header.
[slim L7-14] imports(4): react, @mui/material, ./types, @/lib/api
export default function Page({ id }: { id: string }) {
  [slim L19-23] hooks(4): useState[open, page], useRouter[router], useQuery[data,isLoading]
  const total = useMemo(() => rows.length, [rows]);
  useEffect(() => {
    setOpen(true);
  }, []);
  const opts = [
    { value: 1, label: "a1" },
[slim L31-33] 3 similar lines
    { value: 5, label: "a5" },
  ];
```

Outline:

```
=== src/app/page.tsx outline  42→2 lines, 1.0k→0.1k chars (-86%) ===
   7 [slim L7-14] imports(4): react, @mui/material, ./types, @/lib/api
  18 export default function Page({ id }: { id: string }) {
```

With several files, the last line is the total, e.g. `[slim] total 318 files: 1653.9k→146.6k chars (-91%)`.

## What gets collapsed

| Rule | Collapsed | Never collapsed |
|---|---|---|
| `imports` | 2 or more import / `require` / re-export statements in a row, including multi-line ones, become one module list | A single import; dynamic `import()`; `import.meta`; `export { x }` without `from` |
| `hooks` | 3 or more single-line declaration hooks in a row (`useState`, `useRef`, `useRouter`, `useQuery`, `useForm`, ...) become their variable names | `useEffect`, `useLayoutEffect`, `useInsertionEffect`, `useMemo`, `useCallback`, `useImperativeHandle`, and any hook that spans several lines, because those carry logic |
| `comments` | Block comments and docstrings of 4+ lines, and 4+ `//` or `#` lines in a row, become their first line | Short comments |
| `style` | `<style>` blocks in `.vue` / `.svelte` | `<template>` and `<script>` |
| `similar` | 4+ lines in a row that match except for digits, when hiding them saves over ~40 chars; first and last are kept | Lines that differ in text |
| `long` | Lines over 240 chars are cut to 160 chars plus `…[slim +N chars]` | |
| blank lines | Runs of blank lines become one | |

## When not to use it

- Right before `Edit` or `Write`. Read the exact lines instead.
- Files under ~80 lines. The saving is too small, so use `Read`.
- JSON, YAML, `.env`, SQL, migrations and lockfiles, where every line matters.
- When the user asks to see the exact or full code.
- When the bug may sit in an import or a hook declaration. Use `--keep imports,hooks`, or `Read`.

## Rules

- A placeholder is a summary, not code. Never quote it to the user as code, and never put it in an `Edit` `old_string`.
- If the slim view hides what you need, open the range. Do not guess what is inside a placeholder.
- When you tell the user what a file does, base it on what you actually opened.
