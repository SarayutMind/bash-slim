# ผลทดสอบ A/B รอบ 1 (2026-11-05)

skill เวอร์ชัน `0d13ff2` + `check.sh` (ก่อนแก้ 3 จุด)

สร้างด้วย `python tests/ab.py NORMAL.jsonl SKILL.jsonl` จาก log ของ Claude Code (session ปกติ `cdd9d9cb`, session skill `abcac366`)

## สรุป

| วัดอะไร | ปกติ | skill | ต่าง |
|---|---|---|---|
| API calls (รอบที่ AI คิด) | 26 | 25 | -4% |
| token รวมที่ประมวลผล (input + cache) | 1,885,230 | 1,684,217 | -11% |
| token ที่ AI เขียน (output) | 13,085 | 11,485 | -12% |
| context ตอนเริ่ม | 48,664 | 48,655 | 0% |
| context สูงสุด | 85,815 | 86,533 | +1% |
| context ที่โตขึ้นระหว่างทำงาน | 37,151 | 37,878 | +2% |
| ผลจาก tool ทั้งหมด (ตัวอักษร) | 52,524 | 49,103 | -7% |
| จำนวนครั้งที่เรียก Bash | 17 | 10 | -41% |
| ความยาวคำสั่ง Bash รวม (IN) | 4,397 | 2,064 | -53% |
| output ของ Bash รวม (OUT) | 24,842 | 30,821 | +24% |
| จำนวนครั้งที่ Read | 4 | 9 | +125% |
| ขนาดที่อ่านด้วย Read (ตัวอักษร) | 23,684 | 11,761 | -50% |
| จำนวนครั้งที่ Edit/Write | 7 | 5 | -29% |
| ความยาวคำตอบสุดท้าย (ตัวอักษร) | 2,967 | 2,877 | -3% |
| เรียก `slim.py` / `check.sh` | 0 / 0 | 2 / 1 | |
| ภาษาของคำตอบ | ไทย | อังกฤษ | |

## รายละเอียด: ปกติ

- tools: Bash 17, Edit 7, Glob 1, Grep 2, Read 4, ToolSearch 1, mcp__plugin_context-mode_context-mode__ctx_execute 1
- CLAUDE.md ย่อยที่โหลดระหว่างทำงาน (ตัวอักษร): ไม่มี

| Bash (description) | IN | OUT | บรรทัด |
|---|---|---|---|
| Show recent commits, repo files, package scripts | 99 | 2,061 | 60 |
| Show backoffice validation helpers and API phone helper | 129 | 4,899 | 123 |
| Run Biome lint and turbo typecheck | 164 | 461 | 17 |
| Lint only changed files and check line ending setup | 450 | 1,114 | 25 |
| Run Biome lint with CRLF line endings accepted | 94 | 858 | 15 |
| Commit website validation change | 424 | 709 | 17 |
| Compare working tree diff with and without CR changes | 178 | 1,231 | 13 |
| Show schools page and list API calls in actions | 296 | 322 | 8 |
| List manage-schools files and show page component | 172 | 4,171 | 132 |
| List server actions and API calls on schools page | 450 | 4,257 | 57 |
| Find which list-page components call which actions | 302 | 326 | 3 |
| Show table action imports and filter bar area handling | 224 | 639 | 15 |
| Locate getServerApi definition | 144 | 91 | 1 |
| Show server API client setup and env config | 378 | 1,735 | 50 |
| Show API client base URL, env vars, API listen port | 317 | 1,229 | 30 |
| Probe API and web ports, check env defaults | 472 | 162 | 4 |
| Probe project header API endpoint | 104 | 577 | 1 |

| Read | offset | limit | ตัวอักษร |
|---|---|---|---|
| school-basic-form.tsx | 150 | 250 | 11,705 |
| school-basic-form.tsx | 560 | 90 | 3,499 |
| school-basic-form.tsx | – | 80 | 3,561 |
| schools.schema.ts | – | 130 | 4,919 |

## รายละเอียด: skill

- tools: Bash 10, Edit 5, Glob 1, Grep 6, Read 9, Skill 1, ToolSearch 1, mcp__plugin_context-mode_context-mode__ctx_execute 1
- CLAUDE.md ย่อยที่โหลดระหว่างทำงาน (ตัวอักษร): ไม่มี

| Bash (description) | IN | OUT | บรรทัด |
|---|---|---|---|
| Outline school basic form | 138 | 1,392 | 19 |
| List lint/typecheck scripts | 56 | 158 | 5 |
| Lint + typecheck | 65 | 2,667 | 45 |
| Summarize lint log by diagnostic type | 206 | 198 | 6 |
| Lint summary + lint changed files | 263 | 583 | 17 |
| Show lint summary category headers | 100 | 201 | 2 |
| Commit website validation | 330 | 203 | 3 |
| Map manage-schools feature folder | 95 | 24,764 | 309 |
| Check API URL config and if API is up | 492 | 259 | 7 |
| Test API fetch from Node + dev scripts | 319 | 396 | 1 |

| Read | offset | limit | ตัวอักษร |
|---|---|---|---|
| school-basic-form.tsx | 300 | 50 | 2,521 |
| school-basic-form.tsx | 600 | 30 | 1,088 |
| school-basic-form.tsx | 62 | 12 | 564 |
| school-basic-form.tsx | 163 | 8 | 526 |
| schools.schema.ts | 1 | 40 | 1,605 |
| schools.schema.ts | 39 | 70 | 2,575 |
| page.tsx | – | ทั้งไฟล์ | 86 |
| manage-schools-page.tsx | 35 | 62 | 2,076 |
| session.ts | 70 | 20 | 720 |
