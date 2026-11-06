# bash-slim

![bash-slim: Token compression & output filtering for Claude Code](docs/images/Bash-Slim%201.png)

Plugin สำหรับ Claude Code ที่ทำให้ AI **อ่านน้อยลง ตอบสั้นลง** ช่วยประหยัด token และตอบเร็วขึ้น

## ทำอะไรให้

- **อ่านโค้ดแบบย่อ:** ก่อน AI อ่านไฟล์ จะยุบ import, hook (`useState` ฯลฯ), comment ยาว ๆ และ CSS ให้เหลือบรรทัดเดียว
- **ตอบเฉพาะที่แก้:** AI ไม่พิมพ์โค้ดทั้งไฟล์กลับมา แสดงแค่ส่วนที่เปลี่ยน ที่เหลือแทนด้วย `// ... existing imports/hooks ...`
- **คำสั่งสั้น ผลสั้น:** lint / typecheck / build / test สั่งบรรทัดเดียว ผ่านก็ตอบบรรทัดเดียว พังก็โชว์แค่บรรทัดที่ error

## Input / Workflow / Output

- **Input:** งานไหนก็ได้ในโปรเจกต์ที่ AI ต้องอ่านโค้ดหรือ log, แก้โค้ด หรือรันคำสั่ง เช่น "เพิ่ม validate ในฟอร์ม", "เช็ก lint กับ typecheck", "debug error นี้" พิมพ์สั่งงานตามปกติ ไม่ต้องเรียก skill เอง
- **Output:** คำตอบสั้นที่มี `file:line` แสดงแค่โค้ดที่แก้หรือบรรทัดที่ error ส่วนที่ไม่ได้แก้แทนด้วย placeholder และผลเช็กเหลือบรรทัดเดียว เช่น `✅ fix · ✅ typecheck (51s)`

![Workflow: Read compressed → Edit real code → Reply slim](docs/images/Bash-Slim%203.png)

| ขั้น | Input | ทำอะไร | Output |
|---|---|---|---|
| 1. อ่าน | โฟลเดอร์หรือไฟล์ | `Grep` หาก่อน แล้ว `slim.py` ยุบ import, hook, comment ยาว, CSS | ไฟล์ละบรรทัด, outline ของไฟล์ หรือโค้ดย่อที่มี `[slim L12-30]` บอกว่าซ่อนบรรทัดไหน |
| 2. แก้ | บรรทัดจริงที่เปิดด้วย `Read` (ไม่ใช่ข้อความที่ถูกยุบ) | `Edit` ด้วยโค้ดเต็ม ไม่มี placeholder | ไฟล์ที่แก้แล้ว จอแสดงเฉพาะบรรทัดที่เปลี่ยน |
| 3. เช็ก | ชื่อขั้น เช่น `fix`, `typecheck`, `build`, `test` | `check.sh` รัน biome/prettier เฉพาะไฟล์ที่แก้ และรัน script ใน `package.json` | `✅` บรรทัดเดียว หรือเฉพาะบรรทัด error พร้อม `file:line` และที่อยู่ log เต็ม |
| 4. ตอบ | ผลจากขั้น 1–3 | ตัดโค้ดซ้ำ, import, hook, log | `file:line` + โค้ดที่แก้ + placeholder หรือสถานะบรรทัดเดียว |

## ติดตั้ง

```bash
claude plugin marketplace add SarayutMind/bash-slim
claude plugin install bash-slim@bash-slim
```

แล้วเปิด Claude Code ใหม่ ใช้ได้เลย AI จะใช้เองทุกครั้งโดยไม่ต้องสั่ง

- เครื่องต้องมี `python` 3.8 ขึ้นไป และ `bash` (Windows: ลง Git for Windows ก็มี bash แล้ว)
- อัปเดต: `claude plugin update bash-slim@bash-slim`
- ถอน: `claude plugin uninstall bash-slim@bash-slim`

<details>
<summary>ไม่ใช้ plugin: copy เข้าโปรเจกต์เอง (เช่น อยาก commit ให้ทั้งทีมใช้)</summary>

เปิด terminal ที่ root ของโปรเจกต์ แล้ววางชุดใดชุดหนึ่ง คำสั่งจะ copy skill เข้า `.claude/skills/` และต่อกฎท้าย `CLAUDE.md` ให้

**Mac / Linux / Git Bash**

```bash
tmp=$(mktemp -d) && git clone -q --depth 1 https://github.com/SarayutMind/bash-slim.git "$tmp"
mkdir -p .claude/skills && cp -r "$tmp/.claude/skills/bash-slim" .claude/skills/
printf '\n\n' >> CLAUDE.md && cat "$tmp/CLAUDE.md" >> CLAUDE.md
rm -rf "$tmp"
```

**Windows PowerShell**

```powershell
$tmp = Join-Path $env:TEMP "bash-slim-$(Get-Random)"
git clone -q --depth 1 https://github.com/SarayutMind/bash-slim.git $tmp
New-Item -ItemType Directory -Force .claude\skills | Out-Null
Copy-Item -Recurse -Force "$tmp\.claude\skills\bash-slim" .claude\skills\
Add-Content -Encoding utf8 CLAUDE.md ("`n" + (Get-Content -Raw -Encoding utf8 "$tmp\CLAUDE.md"))
Remove-Item -Recurse -Force $tmp
```

ถอน: ลบโฟลเดอร์ `.claude/skills/bash-slim/` แล้วลบหัวข้อ `## bash-slim: always on` ออกจาก `CLAUDE.md`

</details>

## ก่อน / หลัง

![ก่อนและหลังใช้ bash-slim: จาก 120 บรรทัดเหลือ 8 บรรทัด](docs/images/Bash-Slim%202.png)

### 1. ตอนอ่านไฟล์

ไฟล์ตัวอย่าง [tests/samples/school-page.tsx](tests/samples/school-page.tsx) ยาว 42 บรรทัด ลองรันเองได้ด้วย `python .claude/skills/bash-slim/scripts/slim.py tests/samples/school-page.tsx`

**ไม่มี skill:** AI อ่านทุกบรรทัด ส่วนบนของไฟล์ 19 บรรทัดเป็น comment, import และ hook

```tsx
"use client";
/**
 * School list page.
 * Shows schools with a search box and paging.
 * Data comes from the API through React Query.
 */
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Box, Button, TextField } from "@mui/material";
import { api } from "@/lib/api";
import type { School } from "./types";

export default function SchoolPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();
  const { data = [], isLoading } = useQuery({ queryKey: ["schools", page], queryFn: () => api.schools(page) });
```

**มี skill:** 19 บรรทัดเดียวกันเหลือ 5 บรรทัด แต่ยังรู้ว่ามีอะไรอยู่และอยู่บรรทัดไหน

```
=== tests/samples/school-page.tsx  42→29 lines, 1.3k→0.8k chars (-33%) ===
"use client";
[slim L2-6] comment(5): School list page.
[slim L7-12] imports(6): react, next/navigation, @tanstack/react-query, @mui/material, @/lib/api, ./types

export default function SchoolPage() {
  [slim L15-19] hooks(5): useState[page, search, error], useRouter[router], useQuery[data = [],isLoading]
```

ส่วนที่เหลือ (`useMemo`, `useEffect`, `handleSubmit`, JSX) เหมือนกันทั้งสองแบบ เพราะเป็น logic ที่ AI ต้องใช้ ถ้า AI แค่หาว่าฟังก์ชันอยู่ไหน ใช้ `--outline` เหลือ 3 บรรทัด (−83%):

```
=== tests/samples/school-page.tsx outline  42→3 lines, 1.3k→0.2k chars (-83%) ===
   7 [slim L7-12] imports(6): react, next/navigation, @tanstack/react-query, @mui/material, @/lib/api, ./types
  14 export default function SchoolPage() {
  27   const handleSubmit = async (form: School) => {
```

### 2. ตอนตอบ

**ไม่มี skill:** AI มักพิมพ์ไฟล์กลับมาทั้ง 42 บรรทัด แม้แก้แค่บรรทัดเดียว

**มี skill:** ตอบแค่ส่วนที่แก้ พร้อมบอกไฟล์และบรรทัด

```tsx
// tests/samples/school-page.tsx:28
// ... existing imports/hooks ...
const handleSubmit = async (form: School) => {
  if (total < 0) return setError("ห้ามติดลบ"); // new
  await api.save(form);
  router.refresh();
};
// ... existing JSX ...
```

### 3. ตอนสั่ง "เช็ก lint กับ typecheck"

```
ไม่มี skill   yarn lint 2>&1 | tail -15; echo "=== TYPECHECK ==="; yarn typecheck 2>&1 | tail -25
             → log 34 บรรทัด แล้ว AI เรียกคำสั่งเพิ่มอีก 2 ครั้ง
มี skill      bash .../check.sh
             → ✅ fix · ✅ typecheck (163s)
```

## ผลทดสอบ

### อ่านภาพรวมโปรเจกต์

| โปรเจกต์ | ไม่มี skill | มี skill | ลดลง |
|---|---|---|---|
| Next.js 319 ไฟล์ | 1,676.6k ตัวอักษร | 37.6k | **−98%** |
| Vue 732 ไฟล์ | 9,150.2k ตัวอักษร | 114.8k | **−99%** |

### ทดสอบงานจริง A/B (รอบ 2)

clone โปรเจกต์ Next.js monorepo ของจริงเป็น 2 ชุดจาก commit เดียวกัน ชุดหนึ่งมี skill อีกชุดไม่มี ใช้ model เดียวกัน และส่งข้อความเดียวกันทุกตัวอักษร ให้ทำ 5 งาน: เพิ่ม validate ในฟอร์ม 1,294 บรรทัด → เช็ก lint/typecheck → commit → ถามว่าหน้าเรียก API อะไร → debug error `fetch failed`

| วัดอะไร | ไม่มี skill | มี skill | ต่าง |
|---|---|---|---|
| token รวมที่ประมวลผล | 2,186k | 1,837k | **−16%** |
| token ที่ AI เขียน | 14,534 | 11,374 | **−22%** |
| ผลจาก tool ที่อ่านเข้า context | 62.6k ตัวอักษร | 39.1k | **−38%** |
| จำนวนครั้งที่เรียก Bash | 23 | 8 | **−65%** |
| ความยาวคำสั่ง Bash (IN) | 5,652 ตัวอักษร | 1,887 | **−67%** |
| output ของ Bash (OUT) | 38.0k ตัวอักษร | 5.6k | **−85%** |
| เช็ก lint + typecheck | 34 บรรทัด | 1 บรรทัด | **−97%** |
| log ของ commit | 21 บรรทัด | 4 บรรทัด | **−81%** |
| ความยาวคำตอบสุดท้าย | 3,223 ตัวอักษร | 2,616 | −19% |
| ผลงาน (แก้ฟอร์ม, ตอบ API ครบ 9 ตัว, debug) | ถูกครบ | ถูกครบ | เท่ากัน |

token รวมลดน้อยกว่าส่วนอื่น เพราะส่วนใหญ่เป็น context พื้นฐานของ Claude Code (~48k token ตั้งแต่เริ่ม) ที่ skill ลดไม่ได้ ผลรอบ 1, วิธีทดสอบ, prompt และ script ดึงตัวเลขอยู่ใน [tests/](tests/README.md)

## ข้อจำกัด

- ยุบตามรูปแบบของบรรทัด ไม่ได้ parse โค้ดจริง โค้ดแปลก ๆ อาจยุบไม่ครบ แต่ไม่ได้แก้ไฟล์ จึงไม่ทำให้โค้ดพัง
- กฎเป็นคำสั่งให้ AI ทำตาม ไม่ใช่การบังคับ บางครั้ง AI อาจกลับไปเขียนคำสั่งยาวเอง
- ไฟล์สั้น (~80 บรรทัด), JSON, `.env`, SQL AI จะอ่านตรง ๆ ไม่ผ่านตัวย่อ

## อ่านเพิ่ม

- [รายละเอียด](docs/details.md): อะไรถูกยุบบ้าง, กฎการตอบ, คำสั่งที่ใช้เองได้, ผลทดสอบแต่ละแบบ
- [SKILL.md](.claude/skills/bash-slim/SKILL.md): คำสั่งที่ AI ใช้จริง
