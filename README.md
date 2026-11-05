# bash-slim

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
| โปรเจกต์ Next.js 318 ไฟล์ (outline) | 1,653.9k ตัวอักษร | 146.6k | **−91%** |
| โปรเจกต์ Vue 732 ไฟล์ (outline) | 9,150.2k ตัวอักษร | 538.9k | **−94%** |

## ปัญหาที่แก้

- AI มักพิมพ์โค้ดทั้งไฟล์กลับมาให้ดู ทั้งที่แก้แค่ 2–3 บรรทัด ทำให้เปลือง token, ตอบช้า และหาจุดที่แก้ยาก
- ตอนรอ build หรือ test AI มักพ่น log ยาวออกมาทั้งที่อยากรู้แค่ว่าผ่านหรือไม่ผ่าน
- ปกติ AI จะอ่านไฟล์ด้วย `Read` ทั้งไฟล์ ซึ่งมี import 20 บรรทัด, `useState` 10 บรรทัด และ CSS อีกหลายร้อยบรรทัดติดเข้าไปด้วย ทั้งที่ส่วนใหญ่ไม่ได้ใช้ตอบคำถาม
- ยิ่งโปรเจกต์ใหญ่ AI ยิ่งเปลือง token และ context เต็มเร็ว พอต้องสรุปบทสนทนาบ่อยขึ้นก็ลืมรายละเอียดงาน
- การสั่ง AI ว่า "ไม่ต้องสนใจ import" ไม่ช่วยประหยัด เพราะตอนนั้นไฟล์ถูกอ่านเข้า context ไปแล้ว ต้องกรองก่อนอ่าน ซึ่ง script ของ skill นี้ทำให้

## ไฟล์ใน repo

```
bash-slim/
├── README.md                     ← ไฟล์นี้
├── CLAUDE.md                     ← กฎที่ผูกให้ AI ใช้ skill นี้เองทุกครั้ง
└── .claude/skills/bash-slim/
    ├── SKILL.md                  ← คำสั่งสำหรับ AI: ใช้เมื่อไร, Input, Workflow, Output
    └── scripts/
        └── slim.py               ← ตัวกรองโค้ด (Python 3.8+, ไม่ต้องติดตั้ง library เพิ่ม)
```

รายละเอียดที่ AI ใช้จริงอยู่ใน [SKILL.md](.claude/skills/bash-slim/SKILL.md)

## ติดตั้ง

ต้องมี `python` (Windows) หรือ `python3` (Mac/Linux)

```bash
git clone https://github.com/SarayutMind/bash-slim.git

# 1. copy skill ไปไว้ในโปรเจกต์ที่ต้องการ
mkdir -p <โปรเจกต์ของคุณ>/.claude/skills
cp -r bash-slim/.claude/skills/bash-slim <โปรเจกต์ของคุณ>/.claude/skills/

# 2. ต่อกฎท้าย CLAUDE.md ของโปรเจกต์ ให้ AI ใช้เองโดยไม่ต้องสั่ง
cat bash-slim/CLAUDE.md >> <โปรเจกต์ของคุณ>/CLAUDE.md
```

ถ้าอยากใช้กับทุกโปรเจกต์ ให้ copy โฟลเดอร์ skill ไปไว้ที่ `~/.claude/skills/bash-slim/` แทน แล้วเปลี่ยน path ในกฎของ `CLAUDE.md` เป็น `~/.claude/skills/bash-slim/scripts/slim.py`

จากนั้นเปิด Claude Code ที่ root ของโปรเจกต์ ระบบจะเจอ skill เอง

## วิธีใช้

ปกติไม่ต้องสั่งอะไร เพราะ `CLAUDE.md` บอก AI ให้ใช้เองอยู่แล้ว ถ้าอยากเรียกเองก็พิมพ์ `/bash-slim` หรือสั่งรันตรง ๆ:

| ต้องการ | คำสั่ง |
|---|---|
| ดูภาพรวมทั้งโฟลเดอร์ | `python .claude/skills/bash-slim/scripts/slim.py src/` |
| ดูโครงไฟล์ (ชื่อฟังก์ชัน/component + เลขบรรทัด) | `python .claude/skills/bash-slim/scripts/slim.py src/page.tsx --outline` |
| อ่านทั้งไฟล์แบบยุบแล้ว | `python .claude/skills/bash-slim/scripts/slim.py src/page.tsx` |
| ย่อ log ยาว ๆ | `yarn build 2>&1 \| python .claude/skills/bash-slim/scripts/slim.py -` |
| ดูว่าประหยัดได้เท่าไร | ใส่ `--stats` ต่อท้ายคำสั่ง |
| ไม่ให้ยุบบางอย่าง | `--keep imports,hooks` (ตัวเลือก: imports, hooks, comments, style, similar, long) |

## กฎการแสดงผล (Output Filtering)

| กฎ | รายละเอียด |
|---|---|
| ห้ามพิมพ์โค้ดยาวซ้ำ | imports, hooks และ boilerplate ห้ามพิมพ์ออกมาทั้งหมด |
| ใช้ placeholder | `// ... existing imports/hooks ...`, `{/* ... existing JSX ... */}`, `<!-- ... existing template ... -->`, `/* ... existing styles ... */` |
| แสดงเฉพาะที่สำคัญ | logic หลัก, ฟังก์ชันที่แก้ หรือบรรทัดที่ error พร้อม `file:line` |
| ตอนรอผล | สถานะบรรทัดเดียว เช่น `⏳ build running`, `✅ passed`, `❌ failed: <error แรก>` |
| Bash | รวมหลายขั้นเป็นคำสั่งเดียว, ใช้ flag เงียบ (`-q`, `--silent`), แสดงแค่ผลลัพธ์ |

**ข้อยกเว้น:** placeholder ใช้กับข้อความที่แสดงให้คนอ่านเท่านั้น โค้ดที่เขียนลงไฟล์จริง (Edit/Write), commit และคำสั่ง shell ต้องเป็นโค้ดเต็มเสมอ ไม่งั้นโค้ดจะพัง และถ้าขอดูโค้ดเต็มหรือโค้ดสั้นกว่า ~15 บรรทัด AI จะแสดงทั้งหมด

## Input / Workflow / Output

**Input:** งานใดก็ได้ในโปรเจกต์ที่ต้องอ่านโค้ด/log, แก้โค้ด หรือรันคำสั่ง (ส่วนอ่านโค้ด: path ของไฟล์หรือโฟลเดอร์ หรือ output ของคำสั่งที่ส่งผ่าน `|`)

**Workflow ของ AI:**
1. ดู outline ของโฟลเดอร์เพื่อเลือกไฟล์
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
| โปรเจกต์ Next.js 318 ไฟล์ แบบ outline | 1,653.9k ตัวอักษร | 146.6k | **−91%** |
| โปรเจกต์ Vue 732 ไฟล์ แบบ outline | 9,150.2k ตัวอักษร | 538.9k | **−94%** |
| ไฟล์ตัวอย่าง `.tsx` 42 บรรทัด แบบเต็ม | 1.0k | 0.7k | −32% |
| ไฟล์ตัวอย่าง `.vue` แบบเต็ม | 0.3k | 0.2k | −11% |
| log build ที่ซ้ำกัน 30 บรรทัด | 2.4k | 0.2k | −92% |

**บทเรียนจากการทดสอบ:** เวอร์ชันแรกใส่เลขบรรทัดทุกบรรทัดในโหมดเต็ม ผลคือแทบไม่ประหยัด (Next.js −2%) และ**ใหญ่ขึ้น**ในโปรเจกต์ Vue (+10%) เพราะเลขบรรทัดกินมากกว่าที่ยุบได้ เวอร์ชันนี้จึงปิดเลขบรรทัดในโหมดเต็ม และให้ AI เริ่มจาก outline ซึ่งเป็นจุดที่ประหยัดได้มากที่สุด

**ยังไม่ได้ทดสอบ:**
- Output Filtering: เป้าคือลด token ของคำตอบเกิน 75% แต่ยังไม่ได้วัดจริง (ใช้ตารางด้านล่าง เทียบคำตอบของงานแก้โค้ดชิ้นเดียวกัน)
- โหมดเต็ม (ไม่มีเลขบรรทัด) กับโปรเจกต์จริง
- คุณภาพคำตอบ ว่าใช้ token น้อยลงแล้ว AI ยังตอบถูกเท่าเดิมไหม

วิธีทดสอบคุณภาพ: ถามคำถามเดียวกันกับ 2 session (มีและไม่มี `CLAUDE.md` + skill) แล้วกรอกตารางนี้

| คำถาม | token ที่ใช้ (ปกติ / skill) | ตอบถูกไหม (ปกติ / skill) | ต้องถามซ้ำกี่รอบ (ปกติ / skill) |
|---|---|---|---|
| "component X อยู่ไฟล์ไหน รับ props อะไร" | | | |
| "หน้า Y เรียก API อะไรบ้าง" | | | |
| "อธิบาย flow ของฟอร์ม Z" | | | |

ดู token ที่ใช้ได้ด้วยคำสั่ง `/context` หรือ `/cost` ใน Claude Code

## ข้อจำกัด

- ยุบตามรูปแบบของบรรทัด (regex) ไม่ได้ parse โค้ดจริง ถ้าเขียนโค้ดแปลก ๆ อาจยุบไม่ครบ แต่ไม่ได้แก้ไฟล์ จึงไม่มีผลกับโค้ด
- ไม่เหมาะกับไฟล์สั้นกว่า ~80 บรรทัด, JSON, `.env`, SQL และ migration
- ถ้าบัคอยู่ใน import หรือ hook ให้ใช้ `--keep imports,hooks` หรืออ่านไฟล์ตรง ๆ
