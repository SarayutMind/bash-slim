# bash-slim

![bash-slim: Token compression & output filtering for Claude Code](docs/images/Bash-Slim%201.png)

Agent Skill สำหรับ Claude Code ทำ 2 อย่างเพื่อลด token และให้ AI ตอบเร็วขึ้น

1. **Output Filtering** เวลา AI ตอบ จะไม่พิมพ์ imports, hooks (`useState`, `useEffect`) และ boilerplate ซ้ำ แต่ใช้ placeholder อย่าง `// ... existing imports/hooks ...` แทน แสดงเฉพาะ logic หลัก ฟังก์ชันที่แก้ หรือบรรทัดที่ error และตอนรอคำสั่งจะสรุปสถานะบรรทัดเดียว ไม่พ่น log
2. **Token Compression** เวลา AI อ่านโค้ดด้วย Read/Bash จะยุบ imports, hook ที่เรียงกันยาว, comment ยาว ๆ, `<style>` ของ Vue และบรรทัดซ้ำให้เหลือบรรทัดเดียวแบบ `[slim L12-30] ...` **ก่อน**ที่ข้อความจะเข้าไปใน context

ตัวอย่างคำตอบเมื่อมี skill:

```tsx
// src/features/school/school-form.tsx:42
// ... existing imports/hooks ...
const handleSubmit = async () => {
  if (total < 0) return setError("ห้ามติดลบ"); // new
  await api.save(form);
};
// ... existing JSX ...
```

ตัวอย่างตอนอ่านไฟล์:

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

| ผลทดสอบ | AI ปกติ | มี skill | ลดลง |
|---|---|---|---|
| ภาพรวมโปรเจกต์ Next.js 319 ไฟล์ | 1,676.6k ตัวอักษร | 37.6k | **−98%** |
| ภาพรวมโปรเจกต์ Vue 732 ไฟล์ | 9,150.2k ตัวอักษร | 114.8k | **−99%** |
| ทดสอบงานจริง A/B: output ของ Bash ทั้งงาน | 38.0k ตัวอักษร | 5.6k | **−85%** |
| ทดสอบงานจริง A/B: token รวมทั้งงาน (แก้โค้ด + เช็ก + commit + อ่านโค้ด + debug) | 2,186k | 1,837k | −16% |

## ปัญหาที่แก้

![ก่อนและหลังใช้ bash-slim: จาก 120 บรรทัดเหลือ 8 บรรทัด](docs/images/Bash-Slim%202.png)

- AI มักพิมพ์โค้ดทั้งไฟล์กลับมาให้ดู ทั้งที่แก้แค่ 2–3 บรรทัด ทำให้เปลือง token, ตอบช้า และหาจุดที่แก้ยาก
- ตอนรอ build หรือ test AI มักพ่น log ยาวออกมาทั้งที่อยากรู้แค่ว่าผ่านหรือไม่ผ่าน
- ตอนสั่ง lint/typecheck กล่อง `Bash` บนจอเต็มไปด้วยคำสั่งยาว (python heredoc, `| tail`, `| grep`) และ log หลายสิบบรรทัด
- ปกติ AI จะอ่านไฟล์ด้วย `Read` ทั้งไฟล์ ซึ่งมี import 20 บรรทัด, `useState` 10 บรรทัด และ CSS อีกหลายร้อยบรรทัดติดเข้าไปด้วย ทั้งที่ส่วนใหญ่ไม่ได้ใช้ตอบคำถาม
- ยิ่งโปรเจกต์ใหญ่ AI ยิ่งเปลือง token และ context เต็มเร็ว พอต้องสรุปบทสนทนาบ่อยขึ้นก็ลืมรายละเอียดงาน
- การสั่ง AI ว่า "ไม่ต้องสนใจ import" ไม่ช่วยประหยัด เพราะตอนนั้นไฟล์ถูกอ่านเข้า context ไปแล้ว ต้องกรองก่อนอ่าน ซึ่ง script ของ skill นี้ทำให้

## Bash: คำสั่งสั้น ผลสั้น

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

## ไฟล์ใน repo

```
bash-slim/
├── README.md                     ← ไฟล์นี้
├── CLAUDE.md                     ← กฎที่ผูกให้ AI ใช้ skill นี้เองทุกครั้ง
├── docs/images/                  ← ภาพประกอบ README
└── .claude/skills/bash-slim/
    ├── SKILL.md                  ← คำสั่งสำหรับ AI: ใช้เมื่อไร, Input, Workflow, Output
    └── scripts/
        ├── slim.py               ← ตัวกรองโค้ด (Python 3.8+, ไม่ต้องติดตั้ง library เพิ่ม)
        └── check.sh              ← รัน lint/typecheck/build/test ผ่านบรรทัดเดียว พังโชว์เฉพาะ error (bash)
```

รายละเอียดที่ AI ใช้จริงอยู่ใน [SKILL.md](.claude/skills/bash-slim/SKILL.md)

## ติดตั้ง

ต้องมี `python` (Windows) หรือ `python3` (Mac/Linux) และ `bash` สำหรับ `check.sh` (Windows ใช้ Git Bash)

```bash
git clone https://github.com/SarayutMind/bash-slim.git

# 1. copy skill ไปไว้ในโปรเจกต์ที่ต้องการ
mkdir -p <โปรเจกต์ของคุณ>/.claude/skills
cp -r bash-slim/.claude/skills/bash-slim <โปรเจกต์ของคุณ>/.claude/skills/

# 2. ต่อกฎท้าย CLAUDE.md ของโปรเจกต์ ให้ AI ใช้เองโดยไม่ต้องสั่ง
cat bash-slim/CLAUDE.md >> <โปรเจกต์ของคุณ>/CLAUDE.md
```

ถ้าอยากใช้กับทุกโปรเจกต์ ให้ copy โฟลเดอร์ skill ไปไว้ที่ `~/.claude/skills/bash-slim/` แทน แล้วเปลี่ยน path ในกฎของ `CLAUDE.md` เป็น `~/.claude/skills/bash-slim/scripts/...`

จากนั้นเปิด Claude Code ที่ root ของโปรเจกต์ ระบบจะเจอ skill เอง

## วิธีใช้

ปกติไม่ต้องสั่งอะไร เพราะ `CLAUDE.md` บอก AI ให้ใช้เองอยู่แล้ว ถ้าอยากเรียกเองก็พิมพ์ `/bash-slim` หรือสั่งรันตรง ๆ:

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

## กฎการแสดงผล (Output Filtering)

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

## Input / Workflow / Output

![Workflow: Read compressed → Edit real code → Reply slim](docs/images/Bash-Slim%203.png)

**Input:** งานใดก็ได้ในโปรเจกต์ที่ต้องอ่านโค้ด/log, แก้โค้ด หรือรันคำสั่ง (ส่วนอ่านโค้ด: path ของไฟล์หรือโฟลเดอร์ หรือ output ของคำสั่งที่ส่งผ่าน `|`)

**Workflow ของ AI:**
1. หาของด้วย `Grep` ก่อน หรือดูภาพรวมโฟลเดอร์ (ไฟล์ละบรรทัด) เพื่อเลือกไฟล์
2. ดู outline ของไฟล์เพื่อหาฟังก์ชันที่ต้องการ
3. เปิดอ่านเฉพาะช่วงบรรทัดนั้นด้วย `Read`
4. ถ้าเจอ `[slim L12-30]` แล้วต้องใช้ส่วนนั้น ค่อยเปิดบรรทัด 12–30
5. ก่อนแก้โค้ด ให้อ่านบรรทัดจริงก่อนทุกครั้ง ห้ามแก้จากข้อความที่ถูกยุบ

**Output:** ไฟล์ที่ยุบแล้ว พร้อมหัวบอกขนาดก่อนและหลัง (ตัวอย่างด้านบน) ส่วนโหมด outline จะเหลือแค่ชื่อฟังก์ชันพร้อมเลขบรรทัด:

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

## ผลทดสอบ: AI ปกติ เทียบกับ AI ที่มี skill

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

### ทดสอบงานจริง A/B: AI ปกติ vs AI ที่มี skill

โปรเจกต์ Next.js monorepo จริง (bcp-bmps-app) clone 2 ชุดจาก commit เดียวกัน ชุดหนึ่งมี skill อีกชุดไม่มี ส่งข้อความเดียวกันทุกตัวอักษร (794 ตัวอักษร) ใช้ model เดียวกัน ข้อความมี 5 งาน: เพิ่ม validate เว็บไซต์ในฟอร์ม 1,294 บรรทัด → เช็ก lint/typecheck → commit → ถามว่าหน้าเรียก API อะไร → debug error `fetch failed` ตัวเลขดึงจาก log ของ Claude Code รอบ 2 รีเซ็ตทั้งสองชุดกลับ commit เดิม แล้วส่งข้อความเดิมอีกครั้งหลังแก้ skill

| วัดอะไร | รอบ 1 ปกติ | รอบ 1 skill | รอบ 2 ปกติ | รอบ 2 skill | รอบ 2 ต่าง |
|---|---|---|---|---|---|
| token รวมที่ประมวลผล | 1,885k | 1,684k (−11%) | 2,186k | 1,837k | **−16%** |
| token ที่ AI เขียน | 13,085 | 11,485 (−12%) | 14,534 | 11,374 | **−22%** |
| ผลจาก tool ที่อ่านเข้า context | 52.5k ตัวอักษร | 49.1k (−7%) | 62.6k | 39.1k | **−38%** |
| จำนวนครั้งที่เรียก Bash | 17 | 10 | 23 | 8 | **−65%** |
| ความยาวคำสั่ง Bash (IN) | 4,397 ตัวอักษร | 2,064 | 5,652 | 1,887 | **−67%** |
| output ของ Bash (OUT) | 24.8k ตัวอักษร | 30.8k | 38.0k | 5.6k | **−85%** |
| เช็ก lint + typecheck | 17 บรรทัด | 45 บรรทัด + เรียก Bash อีก 3 ครั้ง | 34 บรรทัด | **1 บรรทัด** | −97% |
| log ของ commit | 17 บรรทัด | 3 บรรทัด | 21 บรรทัด | 4 บรรทัด | −81% |
| ตอบถูก (3 คำถาม) | ถูก (ขาด 1 API) | ถูก (ขาด 1 API) | ถูก ครบ 9 API | ถูก ครบ 9 API | เท่ากัน |
| ภาษาของคำตอบ | ไทย | อังกฤษ | อังกฤษ | ไทย | |

หน้าจอรอบ 2 ตอนสั่ง "เช็ค lint กับ typecheck":

```
ปกติ   IN   yarn lint 2>&1 | tail -15; echo "=== TYPECHECK ==="; yarn typecheck 2>&1 | tail -25
       OUT  34 บรรทัด (diff ของ biome, รายชื่อ package ของ turbo, เวลา) แล้วเรียก Bash อีก 2 ครั้งเพื่อหาว่า error มาจากไหน
skill  IN   bash .claude/skills/bash-slim/scripts/check.sh
       OUT  ✅ fix · ✅ typecheck (163s)
```

หมายเหตุ:
- **รอบ 2 ฝั่ง skill เสียเปรียบ:** session นี้โหลด `CLAUDE.md` ของ `apps/backoffice` และ `apps/api` (36.6k ตัวอักษร ≈ 15k token) เข้ามาเองระหว่างทำงาน และติดอยู่ใน 18 จาก 23 รอบที่ AI ประมวลผล ฝั่งปกติไม่โหลด เพราะเปิด terminal คนละแบบ เรื่องนี้ไม่เกี่ยวกับ skill ถ้าหักออก token รวมจะลดราว **−28%**
- **ฝั่ง skill รอบ 2 lint เฉพาะไฟล์ที่แก้** (`fix`) ไม่ได้ lint ทั้ง repo จึงไม่เห็น error CRLF 444 ตัวที่มีอยู่เดิม ซึ่งไม่เกี่ยวกับงานนี้
- **plugin ย่อคำตอบ (caveman) เปิดทั้งสองฝั่ง** ความยาวคำตอบเลยต่างกันไม่มาก
- **ทดสอบรอบละครั้งต่อฝั่ง** AI ทำงานไม่เหมือนเดิมทุกครั้ง (ฝั่งปกติรอบ 1 ตอบไทย รอบ 2 ตอบอังกฤษ) ตัวเลขจึงขยับได้

**สิ่งที่เจอในรอบ 1 และแก้ก่อนรอบ 2:**

| ปัญหา | ผล | แก้ | รอบ 2 |
|---|---|---|---|
| ดูภาพรวมโฟลเดอร์ 30 ไฟล์ได้ 24.9k ตัวอักษรก้อนเดียว | กิน token เกือบหมดที่ประหยัดได้ | เปลี่ยนเป็นไฟล์ละบรรทัด เหลือ 4.3k (−83%) และแนะนำให้ใช้ `Grep` ก่อน | ได้ 4.1k ✅ |
| lint ทั้ง repo พังเพราะ CRLF, `check.sh` โชว์ diff 40 บรรทัด | AI เรียก Bash เพิ่มอีก 3 ครั้งเพื่อหาสาเหตุ | จัดกลุ่ม error, โชว์ `Found N errors`, บอกว่าเป็น CRLF และไม่ใช่ไฟล์ที่แก้ | AI เลือก lint เฉพาะไฟล์ที่แก้ ผ่าน 1 บรรทัด ✅ (กรณีพังทดสอบด้วยมือแล้ว: 9 บรรทัด) |
| ฝั่ง skill ตอบเป็นภาษาอังกฤษ | กฎเขียนเป็นอังกฤษ AI เลยตอบตาม | เพิ่มกฎ "ตอบภาษาเดียวกับที่ผู้ใช้ถาม" | ตอบไทย ✅ |

**บทเรียนจากการทดสอบ:** เวอร์ชันแรกใส่เลขบรรทัดทุกบรรทัดในโหมดเต็ม ผลคือแทบไม่ประหยัด (Next.js −2%) และ**ใหญ่ขึ้น**ในโปรเจกต์ Vue (+10%) เพราะเลขบรรทัดกินมากกว่าที่ยุบได้ เวอร์ชันนี้จึงปิดเลขบรรทัดในโหมดเต็ม และให้ AI เริ่มจากภาพรวมหรือ outline ซึ่งเป็นจุดที่ประหยัดได้มากที่สุด

**ยังไม่ได้ทดสอบ:** รันซ้ำหลายรอบต่อฝั่งเพื่อดูว่าตัวเลขแกว่งแค่ไหน และทดสอบกับโปรเจกต์ที่ไม่ใช่ Next.js

## ข้อจำกัด

- ยุบตามรูปแบบของบรรทัด (regex) ไม่ได้ parse โค้ดจริง ถ้าเขียนโค้ดแปลก ๆ อาจยุบไม่ครบ แต่ไม่ได้แก้ไฟล์ จึงไม่มีผลกับโค้ด
- ไม่เหมาะกับไฟล์สั้นกว่า ~80 บรรทัด, JSON, `.env`, SQL และ migration
- ถ้าบัคอยู่ใน import หรือ hook ให้ใช้ `--keep imports,hooks` หรืออ่านไฟล์ตรง ๆ
- กล่อง `Bash` และ IN บนจอเป็นของแอป skill ทำได้แค่ให้สั้นลง ซ่อนไม่ได้
- `check.sh` ช่วยเฉพาะงานที่ทำซ้ำบ่อย (lint, typecheck, build, test) คำสั่งอื่นยังต้องพิมพ์เต็ม
- กฎใน `CLAUDE.md` เป็นคำสั่งให้ AI ทำตาม ไม่ใช่การบังคับ บางครั้ง AI อาจกลับไปเขียนคำสั่งยาวเอง
