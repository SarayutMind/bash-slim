# ผลทดสอบ A/B รอบ 2 (2026-11-05)

skill เวอร์ชัน `3f3f545` (หลังแก้ 3 จุด: ภาพรวมโฟลเดอร์ไฟล์ละบรรทัด, `check.sh` สรุป error, ตอบภาษาเดียวกับผู้ใช้)

สร้างด้วย `python tests/ab.py NORMAL.jsonl SKILL.jsonl` จาก log ของ Claude Code (session ปกติ `e1417e62`, session skill `36f7c716`)

## สรุป

| วัดอะไร | ปกติ | skill | ต่าง |
|---|---|---|---|
| API calls (รอบที่ AI คิด) | 29 | 23 | -21% |
| token รวมที่ประมวลผล (input + cache) | 2,185,944 | 1,837,028 | -16% |
| token ที่ AI เขียน (output) | 14,534 | 11,374 | -22% |
| context ตอนเริ่ม | 48,304 | 49,408 | +2% |
| context สูงสุด | 91,555 | 95,822 | +5% |
| context ที่โตขึ้นระหว่างทำงาน | 43,251 | 46,414 | +7% |
| ผลจาก tool ทั้งหมด (ตัวอักษร) | 62,618 | 39,089 | -38% |
| จำนวนครั้งที่เรียก Bash | 23 | 8 | -65% |
| ความยาวคำสั่ง Bash รวม (IN) | 5,652 | 1,887 | -67% |
| output ของ Bash รวม (OUT) | 38,004 | 5,582 | -85% |
| จำนวนครั้งที่ Read | 2 | 10 | +400% |
| ขนาดที่อ่านด้วย Read (ตัวอักษร) | 22,826 | 23,197 | +2% |
| จำนวนครั้งที่ Edit/Write | 8 | 7 | -12% |
| ความยาวคำตอบสุดท้าย (ตัวอักษร) | 3,223 | 2,616 | -19% |
| เรียก `slim.py` / `check.sh` | 0 / 0 | 1 / 1 | |
| ภาษาของคำตอบ | อังกฤษ | ไทย | |

## รายละเอียด: ปกติ

- tools: Bash 23, Edit 8, Grep 1, PowerShell 2, Read 2
- CLAUDE.md ย่อยที่โหลดระหว่างทำงาน (ตัวอักษร): ไม่มี

| Bash (description) | IN | OUT | บรรทัด |
|---|---|---|---|
| Show package scripts and root files | 33 | 1,443 | 52 |
| List workspaces and files mentioning website | 121 | 563 | 17 |
| Find website field and validation in form and API schema | 224 | 719 | 18 |
| Show validation utils and API school schema | 126 | 8,064 | 217 |
| Find website usage in db, api and backoffice sections | 193 | 800 | 9 |
| Run biome lint and turbo typecheck | 83 | 1,167 | 34 |
| Identify lint error kind and compare against clean tree | 291 | 657 | 11 |
| Lint changed files with CRLF line endings allowed | 228 | 43 | 1 |
| Stage the three files and commit | 479 | 989 | 21 |
| Check remaining diff is line endings only | 102 | 1,193 | 10 |
| Recheck status and list manage-schools files | 158 | 3,070 | 39 |
| Show /manage/schools route and page component | 176 | 3,541 | 98 |
| List server actions and API calls used by the page | 467 | 425 | 10 |
| List server actions and API calls used by the page | 448 | 3,940 | 62 |
| Show list call, table imports, filter bar action use | 427 | 1,723 | 45 |
| Check filter bar imports and session helpers | 278 | 1,527 | 24 |
| Check filter bar imports, activity notice use, session API calls | 352 | 689 | 19 |
| Show server API client setup and env URLs | 269 | 2,696 | 78 |
| Find API client base URL and env vars | 219 | 552 | 8 |
| Show API base URL, env files, API port | 306 | 1,261 | 25 |
| Show API env schema, check running servers and docker | 368 | 1,919 | 67 |
| Refresh index so status is clean | 239 | 64 | 1 |
| Show requireRole body | 65 | 959 | 26 |

| Read | offset | limit | ตัวอักษร |
|---|---|---|---|
| school-basic-form.tsx | 1 | 460 | 19,327 |
| school-basic-form.tsx | 560 | 90 | 3,499 |

## รายละเอียด: skill

- tools: Bash 8, Edit 7, Glob 1, Grep 8, Read 10, Skill 1
- CLAUDE.md ย่อยที่โหลดระหว่างทำงาน (ตัวอักษร): `apps\api\CLAUDE.md` (4), `apps\backoffice\CLAUDE.md` (4), `apps\backoffice\AGENTS.md` (6)

| Bash (description) | IN | OUT | บรรทัด |
|---|---|---|---|
| Lint fix + typecheck | 46 | 26 | 1 |
| Commit website validation | 366 | 251 | 4 |
| Map manage-schools feature folder | 95 | 4,131 | 31 |
| Show route file and activities caller | 210 | 159 | 5 |
| Check API env var and which ports listen | 378 | 34 | 2 |
| Check API bind address and listeners | 150 | 226 | 6 |
| Probe API and web dev servers | 212 | 577 | 1 |
| Probe API and web servers with Node fetch | 430 | 178 | 3 |

| Read | offset | limit | ตัวอักษร |
|---|---|---|---|
| validation.ts | – | ทั้งไฟล์ | 3,718 |
| phone.ts | – | ทั้งไฟล์ | 1,417 |
| schools.schema.ts | 1 | 50 | 1,892 |
| school-basic-form.tsx | 20 | 20 | 702 |
| school-basic-form.tsx | 160 | 12 | 786 |
| school-basic-form.tsx | 295 | 40 | 2,123 |
| school-basic-form.tsx | 608 | 32 | 1,354 |
| schools.schema.ts | 50 | 60 | 2,265 |
| manage-schools-page.tsx | – | ทั้งไฟล์ | 3,633 |
| manage-schools.actions.ts | 38 | 135 | 5,307 |
