#!/usr/bin/env python3
"""Compare two Claude Code sessions (A/B test of bash-slim) and print a Markdown report.

Usage:
  python tests/ab.py NORMAL.jsonl SKILL.jsonl > tests/results/roundN.md

Session logs live in ~/.claude/projects/<project-dir>/<session-id>.jsonl.
Numbers come straight from the log: token counts from each API call's `usage`,
sizes from tool inputs and results. No estimation.

Python 3.8+, standard library only.
"""
import json
import os
import sys


def tool_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
    return ""


def analyze(path):
    s = {
        "calls": 0, "out_tok": 0, "total_in": 0, "first_ctx": None, "peak_ctx": 0,
        "result_chars": 0, "bash": [], "reads": [], "edits": 0, "tools": {},
        "slim": 0, "check": 0, "nested": [], "reply": "",
    }
    usage, pending = {}, {}
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    for r in rows:
        if r.get("isSidechain"):
            continue
        msg = r.get("message") or {}
        att = r.get("attachment") or {}
        if att.get("type") == "nested_memory":
            s["nested"].append((att.get("displayPath", "?"), len(att.get("content", ""))))
        if r.get("type") == "assistant":
            if msg.get("usage") and msg.get("id"):
                usage[msg["id"]] = msg["usage"]
            for c in msg.get("content") or []:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "text" and c.get("text", "").strip():
                    s["reply"] = c["text"]
                elif c.get("type") == "tool_use":
                    name, inp = c.get("name"), c.get("input") or {}
                    s["tools"][name] = s["tools"].get(name, 0) + 1
                    if name == "Bash":
                        cmd = inp.get("command", "")
                        rec = {"desc": inp.get("description", ""), "in": len(cmd), "out": 0, "lines": 0}
                        s["bash"].append(rec)
                        pending[c.get("id")] = rec
                        s["slim"] += "slim.py" in cmd
                        s["check"] += "check.sh" in cmd
                    elif name == "Read":
                        rec = {"file": os.path.basename(inp.get("file_path", "")), "offset": inp.get("offset"),
                               "limit": inp.get("limit"), "out": 0}
                        s["reads"].append(rec)
                        pending[c.get("id")] = rec
                    elif name in ("Edit", "Write", "MultiEdit"):
                        s["edits"] += 1
        elif r.get("type") == "user" and isinstance(msg.get("content"), list):
            for c in msg["content"]:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    text = tool_text(c.get("content"))
                    s["result_chars"] += len(text)
                    rec = pending.get(c.get("tool_use_id"))
                    if rec is not None:
                        rec["out"] = len(text)
                        if "lines" in rec:
                            rec["lines"] = text.count("\n") + 1 if text else 0
    for u in usage.values():
        ctx = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
        s["calls"] += 1
        s["out_tok"] += u.get("output_tokens", 0)
        s["total_in"] += ctx
        s["peak_ctx"] = max(s["peak_ctx"], ctx)
        if s["first_ctx"] is None:
            s["first_ctx"] = ctx
    s["first_ctx"] = s["first_ctx"] or 0
    return s


def pct(a, b):
    if not a:
        return "–"
    d = round((b - a) * 100 / a)
    return f"{d:+d}%" if d else "0%"


def lang(text):
    letters = [ch for ch in text if ch.isalpha()]
    thai = sum("฀" <= ch <= "๿" for ch in letters)
    return "ไทย" if letters and thai / len(letters) > 0.2 else "อังกฤษ"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    a, b = analyze(sys.argv[1]), analyze(sys.argv[2])
    num = lambda x: f"{x:,}"
    rows = [
        ("API calls (รอบที่ AI คิด)", a["calls"], b["calls"]),
        ("token รวมที่ประมวลผล (input + cache)", a["total_in"], b["total_in"]),
        ("token ที่ AI เขียน (output)", a["out_tok"], b["out_tok"]),
        ("context ตอนเริ่ม", a["first_ctx"], b["first_ctx"]),
        ("context สูงสุด", a["peak_ctx"], b["peak_ctx"]),
        ("context ที่โตขึ้นระหว่างทำงาน", a["peak_ctx"] - a["first_ctx"], b["peak_ctx"] - b["first_ctx"]),
        ("ผลจาก tool ทั้งหมด (ตัวอักษร)", a["result_chars"], b["result_chars"]),
        ("จำนวนครั้งที่เรียก Bash", len(a["bash"]), len(b["bash"])),
        ("ความยาวคำสั่ง Bash รวม (IN)", sum(x["in"] for x in a["bash"]), sum(x["in"] for x in b["bash"])),
        ("output ของ Bash รวม (OUT)", sum(x["out"] for x in a["bash"]), sum(x["out"] for x in b["bash"])),
        ("จำนวนครั้งที่ Read", len(a["reads"]), len(b["reads"])),
        ("ขนาดที่อ่านด้วย Read (ตัวอักษร)", sum(x["out"] for x in a["reads"]), sum(x["out"] for x in b["reads"])),
        ("จำนวนครั้งที่ Edit/Write", a["edits"], b["edits"]),
        ("ความยาวคำตอบสุดท้าย (ตัวอักษร)", len(a["reply"]), len(b["reply"])),
    ]
    print("| วัดอะไร | ปกติ | skill | ต่าง |")
    print("|---|---|---|---|")
    for label, x, y in rows:
        print(f"| {label} | {num(x)} | {num(y)} | {pct(x, y)} |")
    print(f"| เรียก `slim.py` / `check.sh` | {a['slim']} / {a['check']} | {b['slim']} / {b['check']} | |")
    print(f"| ภาษาของคำตอบ | {lang(a['reply'])} | {lang(b['reply'])} | |")
    for label, s in (("ปกติ", a), ("skill", b)):
        nested = ", ".join(f"`{p}` ({n:,})" for p, n in s["nested"]) or "ไม่มี"
        print(f"\n### {label}\n")
        print(f"- tools: {', '.join(f'{k} {v}' for k, v in sorted(s['tools'].items()))}")
        print(f"- CLAUDE.md ย่อยที่โหลดระหว่างทำงาน (ตัวอักษร): {nested}")
        print("\n| Bash (description) | IN | OUT | บรรทัด |\n|---|---|---|---|")
        for x in s["bash"]:
            print(f"| {x['desc'].replace('|', '/')} | {x['in']:,} | {x['out']:,} | {x['lines']} |")
        print("\n| Read | offset | limit | ตัวอักษร |\n|---|---|---|---|")
        for x in s["reads"]:
            print(f"| {x['file']} | {x['offset'] or '–'} | {x['limit'] or 'ทั้งไฟล์'} | {x['out']:,} |")


if __name__ == "__main__":
    main()
