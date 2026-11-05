#!/usr/bin/env python3
"""bash-slim: print source code with boilerplate collapsed into line-numbered placeholders.

Usage:
  python slim.py FILE [FILE ...]          slim view of each file
  python slim.py DIR                      map: one line per code file, top-level names + line numbers
  python slim.py DIR --outline            detailed outline of every code file under DIR
  python slim.py DIR --full               slim view of every code file under DIR
  python slim.py FILE --outline           signatures only
  some-command 2>&1 | python slim.py -    collapse repeated lines in command output
  python slim.py FILE --stats             only print before/after size
  python slim.py FILE --numbers           slim view with line numbers on every kept line

Placeholders look like `[slim L12-30] imports(14): react, @mui/material, ...`.
L12-30 are the original line numbers, so the hidden text can be opened with
Read(offset=12, limit=19) or `sed -n '12,30p' FILE`. Outline rows always show
their line number.

Python 3.8+, standard library only.
"""
import argparse
import os
import re
import sys

SKIP_DIRS = {
    "node_modules", ".git", ".next", ".nuxt", ".output", ".turbo", ".cache", ".svelte-kit",
    "dist", "build", "out", "coverage", "vendor", "__pycache__", ".venv", "venv", ".idea", ".vscode",
}
LANG_BY_EXT = {
    ".ts": "js", ".tsx": "js", ".js": "js", ".jsx": "js", ".mjs": "js", ".cjs": "js",
    ".vue": "vue", ".svelte": "svelte", ".py": "py",
}
SKIP_FILE_RE = re.compile(r"(\.min\.(js|css)|\.map|\.d\.ts|\.lock|-lock\.json|-lock\.yaml)$")
JS_LIKE = {"js", "vue", "svelte"}
RULES = {"imports", "hooks", "comments", "style", "similar", "long"}

# Hooks that only declare state/refs/context. Logic hooks (useEffect, useMemo,
# useCallback, ...) are never collapsed because their bodies carry behaviour.
LOGIC_HOOKS = {"useEffect", "useLayoutEffect", "useInsertionEffect", "useMemo", "useCallback", "useImperativeHandle"}

RE_JS_IMPORT_START = re.compile(
    r"^\s*(import(?!\s*[(.])\b|export\s+(type\s+)?(\*|\{)|(const|let|var)\s+[\w{}\s,:]+=\s*require\()"
)
RE_JS_IMPORT_END = re.compile(
    r"(\bfrom\s*['\"][^'\"]+['\"]|^\s*import\s*['\"][^'\"]+['\"]|require\(\s*['\"][^'\"]+['\"]\s*\))\s*;?\s*(//.*)?$"
)
RE_PY_IMPORT_START = re.compile(r"^(import\s+[\w.]|from\s+[\w.]+\s+import\b)")
RE_MODULE = re.compile(r"['\"]([^'\"]+)['\"]")
RE_HOOK_LINE = re.compile(
    r"^\s*(?:(?:const|let|var)\s+(?P<lhs>\[[^\]]*\]|\{[^}]*\}|\w+)\s*(?::[^=]+)?=\s*)?"
    r"(?P<hook>use[A-Z]\w*)\s*(?:<[^()]*>)?\(.*\)\s*;?\s*(//.*)?$"
)
RE_OUTLINE = {
    "js": re.compile(
        r"^\s*(export\s+)?(default\s+)?(async\s+)?function\b"
        r"|^\s*(export\s+)?(const|let)\s+\w+\s*(:[^=]+)?=\s*(async\s*)?(\(|function|\w+\s*=>|React\.|memo|forwardRef|styled|create\w*\()"
        r"|^\s*(export\s+)?(default\s+)?(abstract\s+)?class\s+\w+"
        r"|^\s*(export\s+)?(declare\s+)?(interface\s+\w+|enum\s+\w+|type\s+\w+\s*(<[^=]*>)?\s*=)"
        r"|^\s*export\s+default\b"
        r"|^\s*\w+\.(get|post|put|patch|delete|route|use)\(\s*['\"`]"
        r"|^\s*(const\s+\w+\s*=\s*)?define(Props|Emits|Model|Expose)\b"
        r"|^\s*<(template|script|style)\b"
    ),
    "py": re.compile(r"^\s*(async\s+)?def\s+\w+|^\s*class\s+\w+|^@\w+"),
}
# Directory map: the name declared by a top-level outline row.
RE_DECL_NAME = re.compile(
    r"^(?:export\s+)?(?:default\s+)?(?:declare\s+)?(?:abstract\s+)?(?:async\s+)?"
    r"(?:function\*?\s*(\w+)|class\s+(\w+)|(?:const|let|var)\s+(\w+)|interface\s+(\w+)|type\s+(\w+)|enum\s+(\w+))"
)
RE_DEFINE = re.compile(r"^(?:const\s+\w+\s*=\s*)?(define\w+)")
RE_PY_NAME = re.compile(r"^(?:async\s+)?(?:def|class)\s+(\w+)")
MAP_NAMES = 12  # names per file in a directory map


def lang_of(path):
    return LANG_BY_EXT.get(os.path.splitext(path)[1].lower(), "text")


def is_blank(s):
    return not s.strip()


def is_comment_line(s, lang):
    t = s.strip()
    if lang == "py":
        return t.startswith("#")
    if lang in JS_LIKE:
        return t.startswith("//") or (t.startswith("/*") and t.endswith("*/"))
    return False


def short_list(items, limit=10):
    seen = []
    for it in items:
        if it not in seen:
            seen.append(it)
    head = ", ".join(seen[:limit])
    return head + (f", +{len(seen) - limit} more" if len(seen) > limit else "")


def scan_js_statement(lines, k):
    """Return end index (exclusive) of an import/re-export/require statement starting at k, or None."""
    for j in range(k, min(k + 80, len(lines))):
        line = lines[j]
        if RE_JS_IMPORT_END.search(line):
            return j + 1
        # `export { a, b }` without `from`, or any statement that closes without a module path
        if "}" in line and j > k or line.rstrip().endswith(";"):
            return None
        if j == k and "}" in line:
            return None
    return None


def scan_py_statement(lines, k):
    j = k
    depth = lines[k].count("(") - lines[k].count(")")
    while (depth > 0 or lines[j].rstrip().endswith("\\")) and j + 1 < len(lines):
        j += 1
        depth += lines[j].count("(") - lines[j].count(")")
    return j + 1


def scan_imports(lines, i, lang):
    """Collapse a run of import statements. Returns (end_exclusive, modules, statements)."""
    if lang in JS_LIKE:
        start_re, scan = RE_JS_IMPORT_START, scan_js_statement
    elif lang == "py":
        start_re, scan = RE_PY_IMPORT_START, scan_py_statement
    else:
        return i, [], 0
    mods, stmts, j, last_end = [], 0, i, i
    while j < len(lines):
        line = lines[j]
        if start_re.match(line):
            end = scan(lines, j)
            if end is None:
                break
            text = " ".join(lines[j:end])
            if lang == "py":
                m = re.match(r"^\s*(?:from\s+([\w.]+)|import\s+([\w.]+))", text)
                mods.append((m.group(1) or m.group(2)) if m else "?")
            else:
                found = RE_MODULE.findall(text)
                mods.append(found[-1] if found else "?")
            stmts += 1
            j = last_end = end
        elif is_blank(line) or is_comment_line(line, lang):
            j += 1
        else:
            break
    return last_end, mods, stmts


def block_comment_end(lines, i, lang):
    """If a multi-line comment/docstring starts at i, return its end index (exclusive)."""
    t = lines[i].strip()
    if lang in JS_LIKE and t.startswith("/*") and "*/" not in t:
        for j in range(i + 1, len(lines)):
            if "*/" in lines[j]:
                return j + 1
    if lang == "py":
        for q in ('"""', "'''"):
            if t.startswith(q) and t.count(q) == 1:
                for j in range(i + 1, len(lines)):
                    if q in lines[j]:
                        return j + 1
    return None


def first_text(chunk):
    for raw in chunk:
        t = re.sub(r"^[\s/*#\"']+|[\s*/\"']+$", "", raw)
        if t:
            return t[:80]
    return ""


def hook_name(m):
    lhs = m.group("lhs")
    if not lhs:
        return "-"
    if lhs.startswith("["):
        return lhs.strip("[]").split(",")[0].strip() or "-"
    if lhs.startswith("{"):
        return ",".join(p.split(":")[0].strip() for p in lhs.strip("{}").split(",") if p.strip())
    return lhs


def norm_similar(s):
    return re.sub(r"\d+", "#", s.strip())


def slim(lines, lang, keep, min_run):
    """Return list of rows: (lineno, text) for kept lines or (start, text) placeholders."""
    out = []
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]

        # Vue/Svelte <style> blocks
        if "style" not in keep and lang in ("vue", "svelte") and re.match(r"^\s*<style\b", line):
            j = i
            while j < n - 1 and "</style>" not in lines[j]:
                j += 1
            out.append((i + 1, f"[slim L{i + 1}-{j + 1}] {line.strip()} … </style> ({j - i + 1} lines)"))
            i = j + 1
            continue

        # import blocks
        if "imports" not in keep:
            end, mods, stmts = scan_imports(lines, i, lang)
            if stmts >= 2:
                out.append((i + 1, f"[slim L{i + 1}-{end}] imports({stmts}): {short_list(mods)}"))
                i = end
                continue

        # long block comments / docstrings
        if "comments" not in keep:
            end = block_comment_end(lines, i, lang)
            if end and end - i >= 4:
                out.append((i + 1, f"[slim L{i + 1}-{end}] comment({end - i}): {first_text(lines[i:end])}"))
                i = end
                continue
            # runs of single-line comments (often commented-out code)
            j = i
            while j < n and is_comment_line(lines[j], lang) and not lines[j].strip().startswith("/*"):
                j += 1
            if j - i >= 4:
                out.append((i + 1, f"[slim L{i + 1}-{j}] comment lines({j - i}): {first_text(lines[i:j])}"))
                i = j
                continue

        # runs of state/ref/context hook declarations
        if "hooks" not in keep and lang in JS_LIKE:
            j, found, last = i, [], i
            while j < n:
                m = RE_HOOK_LINE.match(lines[j])
                if m and m.group("hook") not in LOGIC_HOOKS:
                    found.append((m.group("hook"), hook_name(m)))
                    j += 1
                    last = j
                elif is_blank(lines[j]) and found:
                    j += 1
                else:
                    break
            if len(found) >= min_run:
                groups = {}
                for hk, name in found:
                    groups.setdefault(hk, []).append(name)
                summary = ", ".join(f"{hk}[{short_list(v, 8)}]" for hk, v in groups.items())
                indent = re.match(r"^\s*", line).group(0)
                out.append((i + 1, f"{indent}[slim L{i + 1}-{last}] hooks({len(found)}): {summary}"))
                i = last
                continue

        # runs of near-identical lines (digits ignored): keep first and last
        if "similar" not in keep and not is_blank(line):
            key = norm_similar(line)
            j = i + 1
            while j < n and not is_blank(lines[j]) and norm_similar(lines[j]) == key:
                j += 1
            # only when the hidden lines outweigh the ~40-char placeholder
            if j - i >= 4 and (j - i - 2) * len(key) > 40:
                out.append((i + 1, clip(line, keep)))
                out.append((i + 2, f"[slim L{i + 2}-{j - 1}] {j - i - 2} similar lines"))
                out.append((j, clip(lines[j - 1], keep)))
                i = j
                continue

        # collapse blank runs to one blank
        if is_blank(line):
            if out and out[-1][1] == "":
                i += 1
                continue
            out.append((i + 1, ""))
            i += 1
            continue

        out.append((i + 1, clip(line, keep)))
        i += 1
    return out


def clip(line, keep):
    if "long" in keep or len(line) <= 240:
        return line
    return f"{line[:160]} …[slim +{len(line) - 160} chars]"


def outline(lines, lang, keep):
    out = []
    skip = range(0)
    if "imports" not in keep:
        # first import block, wherever it starts (after a directive, header comment, or <script>)
        for k in range(len(lines)):
            end, mods, stmts = scan_imports(lines, k, lang)
            if stmts:
                out.append((k + 1, f"[slim L{k + 1}-{end}] imports({stmts}): {short_list(mods)}"))
                skip = range(k, end)
                break
    pattern = RE_OUTLINE.get("js" if lang in JS_LIKE else lang)
    if pattern:
        for idx, line in enumerate(lines):
            if idx not in skip and pattern.match(line):
                text = line.rstrip()
                out.append((idx + 1, text if len(text) <= 160 else text[:160] + " …"))
    return out


def top_names(lines, lang):
    """(line, name) of each top-level function, component, class or type."""
    names = []
    pattern = RE_OUTLINE.get("js" if lang in JS_LIKE else lang)
    for idx, line in enumerate(lines):
        if not line or line[0].isspace():
            continue
        if lang == "py":
            m = RE_PY_NAME.match(line)
            if m:
                names.append((idx + 1, m.group(1)))
            continue
        if not (pattern and pattern.match(line)):
            continue
        m = RE_DECL_NAME.match(line)
        if m:
            names.append((idx + 1, next(g for g in m.groups() if g)))
        elif line.startswith("export default"):
            names.append((idx + 1, "default"))
        else:
            m = RE_DEFINE.match(line)
            if m:
                names.append((idx + 1, m.group(1)))
    return names


def map_line(rel, lines, lang):
    names = top_names(lines, lang)
    shown = " · ".join(f"{ln} {name}" for ln, name in names[:MAP_NAMES])
    more = f" · +{len(names) - MAP_NAMES}" if len(names) > MAP_NAMES else ""
    return f"{rel} ({len(lines)})" + (f"  {shown}{more}" if shown else "")


def read_text(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", errors="replace").splitlines()


def render(rows, numbers):
    if numbers:
        return "\n".join(f"{ln:>4} {text}" if text else "" for ln, text in rows)
    return "\n".join(text for _, text in rows)


def walk(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (d.startswith(".") and d != ".claude"))
        for name in sorted(files):
            if lang_of(name) != "text" and not SKIP_FILE_RE.search(name):
                yield os.path.join(base, name)


def main():
    ap = argparse.ArgumentParser(description="Token-saving code viewer (bash-slim).")
    ap.add_argument("paths", nargs="+", help="files, directories, or - for stdin")
    ap.add_argument("--outline", action="store_true",
                    help="signatures only; for a directory, a detailed outline of every file instead of the one-line map")
    ap.add_argument("--full", action="store_true", help="slim view even for directories")
    ap.add_argument("--keep", default="", help=f"comma list of rules to switch off: {','.join(sorted(RULES))}")
    ap.add_argument("--lang", default=None, help="force language for stdin/unknown files: js|vue|py|text")
    ap.add_argument("--min-run", type=int, default=3, help="min hook declarations to collapse (default 3)")
    ap.add_argument("--max-files", type=int, default=None, help="cap files per directory (default 300 for a map, 60 otherwise)")
    ap.add_argument("--numbers", action="store_true",
                    help="prefix kept lines with line numbers in slim view (outline always has them; costs ~5 chars/line)")
    ap.add_argument("--stats", action="store_true", help="only print size before/after")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    keep = {k.strip() for k in args.keep.split(",") if k.strip()}
    unknown = keep - RULES
    if unknown:
        ap.error(f"unknown --keep rule(s): {', '.join(sorted(unknown))}")

    jobs = []  # (label, lines, lang, outline_mode); lines None = print label as is
    for p in args.paths:
        if p == "-":
            jobs.append(("<stdin>", sys.stdin.read().splitlines(), args.lang or "text", args.outline))
        elif os.path.isdir(p):
            files = list(walk(p))
            as_map = not (args.outline or args.full)
            cap = args.max_files or (300 if as_map else 60)
            rows, before = [], 0
            for f in files[:cap]:
                lines = read_text(f)
                if lines is None:
                    continue
                if as_map:
                    rows.append(map_line(os.path.relpath(f, p).replace(os.sep, "/"), lines, args.lang or lang_of(f)))
                    before += sum(len(l) + 1 for l in lines)
                    continue
                try:
                    label = os.path.relpath(f)
                except ValueError:  # different drive on Windows
                    label = f
                jobs.append((label, lines, args.lang or lang_of(f), True if args.outline else not args.full))
            more = f"[slim] +{len(files) - cap} more files under {p} (raise --max-files)" if len(files) > cap else ""
            if as_map:
                body = "\n".join(rows + ([more] if more else []))
                after = len(body) + 1
                head = (f"=== {p} map: {len(rows)} files, {before / 1000:.1f}k→{after / 1000:.1f}k chars "
                        f"({change(before, after)}) · file (lines)  line name · --outline for detail ===")
                jobs.append((head + ("" if args.stats else "\n" + body), None, None, None))
            elif more:
                jobs.append((more, None, None, None))
        elif os.path.isfile(p):
            lines = read_text(p)
            if lines is None:
                print(f"=== {p}: binary, skipped ===")
                continue
            jobs.append((p, lines, args.lang or lang_of(p), args.outline))
        else:
            print(f"=== {p}: not found ===")

    tot_before = tot_after = files_done = 0
    for label, lines, lang, outline_mode in jobs:
        if lines is None:
            print(label)
            continue
        rows = outline(lines, lang, keep) if outline_mode else slim(lines, lang, keep, args.min_run)
        # Line numbers cost more than the collapsing saves on a full view, so they are
        # opt-in there; placeholders still carry their L-ranges.
        body = render(rows, outline_mode or (args.numbers and label != "<stdin>"))
        before = sum(len(l) + 1 for l in lines)
        after = len(body) + 1
        tot_before += before
        tot_after += after
        files_done += 1
        mode = " outline" if outline_mode else ""
        print(f"=== {label}{mode}  {len(lines)}→{len(rows)} lines, {before / 1000:.1f}k→{after / 1000:.1f}k chars ({change(before, after)}) ===")
        if not args.stats:
            print(body)
    if files_done > 1:
        print(f"[slim] total {files_done} files: {tot_before / 1000:.1f}k→{tot_after / 1000:.1f}k chars ({change(tot_before, tot_after)})")


def change(before, after):
    if not before:
        return "0%"
    pct = round((after - before) * 100 / before)
    return f"{pct:+d}%"


if __name__ == "__main__":
    main()
