# bash-slim: รายละเอียด

หน้านี้เก็บรายละเอียดที่ไม่ได้อยู่ใน [README](../README.md) คำสั่งที่ AI ใช้จริงอยู่ใน [SKILL.md](../.claude/skills/bash-slim/SKILL.md)

## คำสั่งที่ใช้เองได้

ปกติไม่ต้องสั่งอะไร AI ใช้เอง ถ้าอยากเรียก skill เองให้พิมพ์ `/bash-slim:bash-slim` (ติดตั้งแบบ plugin) หรือ `/bash-slim` (แบบ copy เข้าโปรเจกต์)

path ในตารางเป็นของแบบ copy เข้าโปรเจกต์ ถ้าติดตั้งแบบ plugin AI จะใช้ path ของ plugin ให้เอง

| ต้องการ | คำสั่ง |
|---|---|
| ดูภาพรวมทั้งโฟลเดอร์ (ไฟล์ละบรรทัด: จำนวนบรรทัด + ชื่อฟังก์ชัน/component) | `python .claude/skills/bash-slim/scripts/slim.py src/` |
| ดูโครงไฟล์ (ชื่อฟังก์ชัน/component + เลขบรรทัด) | `python .claude/skills/bash-slim/scripts/slim.py src/page.tsx --outline` |
| อ่านทั้งไฟล์แบบยุบแล้ว | `python .claude/skills/bash-slim/scripts/slim.py src/page.tsx` |
| ย่อ log ยาว ๆ | `yarn build 2>&1 \| python .claude/skills/bash-slim/scripts/slim.py -` |
| ดูว่าประหยัดได้เท่าไร | ใส่ `--stats` ต่อท้ายคำสั่ง |
| ไม่ให้ยุบบางอย่าง | `--keep imports,hooks` (ตัวเลือก: imports, hooks, comments, style, similar, long) |
| lint + typecheck | `bash .claude/skills/bash-slim/scripts/check.sh` |
| รัน script อื่นใน package.json | `bash .claude/skills/bash-slim/scripts/check.sh build test` |
| รันคำสั่งเอง | `bash .claude/skills/bash-slim/scripts/check.sh 'api=yarn workspace @repo/api typecheck'` |

## ตัวอย่างตอนอ่านไฟล์

```
=== src/app/page.tsx  42→25 lines, 1.0k→0.7k chars (-32%) ===
"use client";
[slim L2-6] comment(5): Page header.
[slim L7-14] imports(4): react, @mui/material, ./types, @/lib/api
export default function Page({ id }: { id: string }) {
  [slim L19-23] hooks(4): useState[open, page], useRouter[router], useQuery[data,isLoading]
  const total = useMemo(() => rows.length, [rows]);
  useEffect(() => {
```

โหมด outline เหลือแค่ชื่อฟังก์ชันพร้อมเลขบรรทัด:

```
=== src/app/page.tsx outline  42→2 lines, 1.0k→0.1k chars (-86%) ===
   7 [slim L7-14] imports(4): react, @mui/material, ./types, @/lib/api
  18 export default function Page({ id }: { id: string }) {
```

ภาพรวมโฟลเดอร์ (ไฟล์ละบรรทัด):

```
=== features/manage-schools map: 30 files, 275.5k→4.0k chars (-99%) ===
components/school-basic-form.tsx (1302)  106 gradeOptions · 110 gradesReversed · 122 SchoolBasicForm
page/manage-schools-page.tsx (96)  16 readFilters · 35 ManageSchoolsPage
sections/manage-schools.actions.ts (440)  38 getSchoolList · 63 getSchoolSummary · 75 getSchoolFilterOptions · … · +19
```

## สิ่งที่ถูกยุบ และสิ่งที่ไม่ยุบ

| ประเภท | ยุบ | ไม่ยุบ |
|---|---|---|
| imports | import ตั้งแต่ 2 บรรทัดที่อยู่ติดกัน (รวม import หลายบรรทัด) เหลือแค่รายชื่อ module | import บรรทัดเดียว, `import()`, `import.meta` |
| hooks | `useState`, `useRef`, `useRouter`, `useQuery` ฯลฯ ที่เขียนบรรทัดเดียวและเรียงกันตั้งแต่ 3 ตัว เหลือแค่ชื่อตัวแปร | `useEffect`, `useMemo`, `useCallback` และ hook ที่เขียนหลายบรรทัด เพราะมี logic อยู่ข้างใน |
| comments | comment หรือ docstring ตั้งแต่ 4 บรรทัด เหลือแค่บรรทัดแรก | comment สั้น |
| style | `<style>` ในไฟล์ `.vue` / `.svelte` | `<template>`, `<script>` |
| similar | บรรทัดที่ต่างกันแค่ตัวเลข เรียงกันตั้งแต่ 4 บรรทัด เก็บไว้แค่บรรทัดแรกกับบรรทัดสุดท้าย | บรรทัดที่ข้อความต่างกัน |
| long | บรรทัดที่ยาวเกิน 240 ตัวอักษร ตัดเหลือ 160 | |

## กฎการตอบของ AI

| กฎ | รายละเอียด |
|---|---|
| ห้ามพิมพ์โค้ดยาวซ้ำ | imports, hooks และ boilerplate ห้ามพิมพ์ออกมาทั้งหมด |
| ใช้ placeholder | `// ... existing imports/hooks ...`, `{/* ... existing JSX ... */}`, `<!-- ... existing template ... -->`, `/* ... existing styles ... */` |
| แสดงเฉพาะที่สำคัญ | logic หลัก, ฟังก์ชันที่แก้ หรือบรรทัดที่ error พร้อม `file:line` |
| ตอนรอผล | สถานะบรรทัดเดียว เช่น `⏳ build running`, `✅ passed`, `❌ failed: <error แรก>` |
| Bash | รวมหลายขั้นเป็นคำสั่งเดียว ถ้าสำเร็จแสดงบรรทัดเดียว (เช่น `331555b [FIX] Page size 100`) ตัด warning CRLF และ log ของ husky/lint-staged ทิ้ง ถ้าพังแสดง log เต็มให้เห็น error |
| lint / typecheck / build / test | ใช้ `check.sh` คำสั่งบรรทัดเดียว ผลบรรทัดเดียว ไม่ต่อ `\| tail` `\| grep` เอง |
| แก้ไฟล์ | ใช้ `Edit` ห้ามใช้ `python - <<'EOF'`, `sed -i` หรือ heredoc ใน Bash เพราะโค้ดทั้งก้อนจะไปโผล่ใน IN |

**ข้อยกเว้น:** placeholder ใช้กับข้อความที่แสดงให้คนอ่านเท่านั้น โค้ดที่เขียนลงไฟล์จริง (Edit/Write), commit และคำสั่ง shell ต้องเป็นโค้ดเต็มเสมอ ไม่งั้นโค้ดจะพัง และถ้าขอดูโค้ดเต็มหรือโค้ดสั้นกว่า ~15 บรรทัด AI จะแสดงทั้งหมด

## ขั้นตอนที่ AI ทำ

![Workflow: Read compressed → Edit real code → Reply slim](images/Bash-Slim%203.png)

1. หาของด้วย `Grep` ก่อน หรือดูภาพรวมโฟลเดอร์ (ไฟล์ละบรรทัด) เพื่อเลือกไฟล์
2. ดู outline ของไฟล์เพื่อหาฟังก์ชันที่ต้องการ
3. เปิดอ่านเฉพาะช่วงบรรทัดนั้นด้วย `Read`
4. ถ้าเจอ `[slim L12-30]` แล้วต้องใช้ส่วนนั้น ค่อยเปิดบรรทัด 12–30
5. ก่อนแก้โค้ด ให้อ่านบรรทัดจริงก่อนทุกครั้ง ห้ามแก้จากข้อความที่ถูกยุบ

## check.sh

ทุกครั้งที่ AI รัน Bash จอจะแสดงกล่องที่มีคำสั่ง (IN) และผลลัพธ์ (OUT) กล่องนี้แอปเป็นคนแสดง skill ซ่อนไม่ได้ แต่ทำให้ทั้ง IN และ OUT สั้นลงได้

ก่อน (IN ~15 บรรทัด, OUT สูงสุด 28 บรรทัดแม้จะผ่าน):

```
Bash  Add type import, lint, typecheck both apps
  IN   python - <<'EOF'
       def edit(p, pairs): ...
       EOF
       cd ... && yarn biome check --write $(git diff --name-only) ... | tail -15; yarn workspace @repo/api typecheck 2>&1 | tail -3; ...
  OUT  log ของ biome และ typecheck
```

หลัง: แก้ไฟล์ด้วย `Edit` (จอแสดงเฉพาะบรรทัดที่แก้) แล้วเช็กด้วย `check.sh`

```
Bash  Lint + typecheck
  IN   bash .claude/skills/bash-slim/scripts/check.sh
  OUT  ✅ fix · ✅ typecheck (51s)
```

ถ้าพัง จะแสดงเฉพาะบรรทัด error พร้อม `file:line` และที่อยู่ของ log เต็ม:

```
❌ fix · ✅ api · ❌ backoffice (14s)

── ❌ backoffice ──
src/app/features/manage-schools/components/school-year-forms.tsx(1056,14): error TS2322: Type 'string' is not assignable to type 'number'.
… 1 of 3 lines, full log: C:/Users/<you>/AppData/Local/Temp/bash-slim/backoffice.log
```

`check.sh` ไม่ต้องตั้งค่า: หา package manager (yarn/pnpm/npm/bun) จาก lockfile, `fix` ใช้ biome (หรือ prettier/eslint) `--write` กับไฟล์ที่แก้เท่านั้นแบบเดียวกับ lint-staged, ชื่ออื่นจะรัน script ใน `package.json` และใส่คำสั่งเองได้ด้วย `ชื่อ=คำสั่ง`

## ผลทดสอบแต่ละแบบ

วัดเป็นจำนวนตัวอักษรที่ AI ต้องอ่านเข้า context ซึ่งจำนวน token แปรผันตามตัวอักษร

| การทดสอบ | AI ปกติ (`Read` ทั้งไฟล์) | มี skill | ลดลง |
|---|---|---|---|
| โปรเจกต์ Next.js 319 ไฟล์ ภาพรวมโฟลเดอร์ (ไฟล์ละบรรทัด) | 1,676.6k ตัวอักษร | 37.6k | **−98%** |
| โปรเจกต์ Vue 732 ไฟล์ ภาพรวมโฟลเดอร์ (ไฟล์ละบรรทัด) | 9,150.2k ตัวอักษร | 114.8k | **−99%** |
| โปรเจกต์ Next.js 319 ไฟล์ outline ละเอียดทุกไฟล์ (`--outline`) | 1,676.6k | 144.3k | −91% |
| โปรเจกต์ Vue 732 ไฟล์ outline ละเอียดทุกไฟล์ (`--outline`) | 9,150.2k | 538.9k | −94% |
| ไฟล์ตัวอย่าง `.tsx` 42 บรรทัด แบบเต็ม | 1.0k | 0.7k | −32% |
| ไฟล์ตัวอย่าง `.vue` แบบเต็ม | 0.3k | 0.2k | −11% |
| log build ที่ซ้ำกัน 30 บรรทัด | 2.4k | 0.2k | −92% |

`check.sh` ทดสอบกับโปรเจกต์ Next.js monorepo จริง (turbo, biome, 6 packages):

| กรณี | OUT ที่เห็น |
|---|---|
| ไม่มีไฟล์แก้ typecheck ผ่าน | `– fix (no changed files) · ✅ typecheck (51s)` 1 บรรทัด |
| type error 1 จุด | สรุป 1 บรรทัด + error 5 บรรทัด (log จริง 19 บรรทัด) |
| biome error + type error, แยก typecheck 2 app | สรุป 1 บรรทัด + error ของแต่ละขั้น (biome 7 จาก 20, typecheck 1 จาก 3) |
| ชื่อ step ที่ไม่มี | `❌ nope` + `no "nope" script in package.json` |
| lint ทั้ง repo พังเพราะ CRLF (441 errors) + type error | lint 9 บรรทัด: จัดกลุ่ม `format ×20`, `Found 441 errors`, บอกว่าเป็น CRLF และไม่ใช่ไฟล์ที่แก้ (เดิม 40 บรรทัด) |

ทดสอบงานจริง A/B (AI ปกติ vs AI ที่มี skill ทำงานเดียวกัน) ดูวิธีทดสอบและตัวเลขทั้งหมดใน [tests/](../tests/README.md)

**บทเรียนจากการทดสอบ:** เวอร์ชันแรกใส่เลขบรรทัดทุกบรรทัดในโหมดเต็ม ผลคือแทบไม่ประหยัด (Next.js −2%) และ**ใหญ่ขึ้น**ในโปรเจกต์ Vue (+10%) เพราะเลขบรรทัดกินมากกว่าที่ยุบได้ เวอร์ชันนี้จึงปิดเลขบรรทัดในโหมดเต็ม และให้ AI เริ่มจากภาพรวมหรือ outline ซึ่งเป็นจุดที่ประหยัดได้มากที่สุด

**ยังไม่ได้ทดสอบ:** รันซ้ำหลายรอบต่อฝั่งเพื่อดูว่าตัวเลขแกว่งแค่ไหน และทดสอบกับโปรเจกต์ที่ไม่ใช่ Next.js

## ข้อจำกัดทั้งหมด

- ยุบตามรูปแบบของบรรทัด (regex) ไม่ได้ parse โค้ดจริง ถ้าเขียนโค้ดแปลก ๆ อาจยุบไม่ครบ แต่ไม่ได้แก้ไฟล์ จึงไม่มีผลกับโค้ด
- ไม่เหมาะกับไฟล์สั้นกว่า ~80 บรรทัด, JSON, `.env`, SQL และ migration
- ถ้าบัคอยู่ใน import หรือ hook ให้ใช้ `--keep imports,hooks` หรืออ่านไฟล์ตรง ๆ
- กล่อง `Bash` และ IN บนจอเป็นของแอป skill ทำได้แค่ให้สั้นลง ซ่อนไม่ได้
- `check.sh` ช่วยเฉพาะงานที่ทำซ้ำบ่อย (lint, typecheck, build, test) คำสั่งอื่นยังต้องพิมพ์เต็ม
- กฎ (จาก plugin หรือ `CLAUDE.md`) เป็นคำสั่งให้ AI ทำตาม ไม่ใช่การบังคับ บางครั้ง AI อาจกลับไปเขียนคำสั่งยาวเอง

## ไฟล์ใน repo

```
bash-slim/
├── README.md                     ← หน้าแรก
├── CLAUDE.md                     ← กฎที่ผูกให้ AI ใช้ skill นี้เองทุกครั้ง
├── .claude-plugin/               ← plugin.json + marketplace.json ให้ติดตั้งผ่าน `claude plugin install` ได้
├── hooks/                        ← hook ตอนเริ่ม session: ส่งกฎใน CLAUDE.md ให้ AI โดยเปลี่ยน path เป็นของ plugin
├── docs/                         ← หน้านี้ + ภาพประกอบ
├── tests/                        ← ทดสอบ A/B: prompt, script ดึงตัวเลขจาก log, ผลรอบ 1 และ 2, ไฟล์ตัวอย่างใน samples/
└── .claude/skills/bash-slim/
    ├── SKILL.md                  ← คำสั่งสำหรับ AI: ใช้เมื่อไร, Input, Workflow, Output
    └── scripts/
        ├── slim.py               ← ตัวกรองโค้ด (Python 3.8+, ไม่ต้องติดตั้ง library เพิ่ม)
        └── check.sh              ← รัน lint/typecheck/build/test ผ่านบรรทัดเดียว พังโชว์เฉพาะ error (bash)
```
