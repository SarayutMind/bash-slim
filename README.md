# bash-slim

![bash-slim: Token compression & output filtering for Claude Code](docs/images/Bash-Slim%201.png)

Plugin สำหรับ Claude Code ที่ทำให้ AI **อ่านน้อยลง ตอบสั้นลง** ช่วยประหยัด token และตอบเร็วขึ้น

## ทำอะไรให้

- **อ่านโค้ดแบบย่อ:** ก่อน AI อ่านไฟล์ จะยุบ import, hook (`useState` ฯลฯ), comment ยาว ๆ และ CSS ให้เหลือบรรทัดเดียว
- **ตอบเฉพาะที่แก้:** AI ไม่พิมพ์โค้ดทั้งไฟล์กลับมา แสดงแค่ส่วนที่เปลี่ยน ที่เหลือแทนด้วย `// ... existing imports/hooks ...`
- **คำสั่งสั้น ผลสั้น:** lint / typecheck / build / test สั่งบรรทัดเดียว ผ่านก็ตอบบรรทัดเดียว พังก็โชว์แค่บรรทัดที่ error

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

AI แก้โค้ดเสร็จ ตอบแค่ส่วนที่แก้:

```tsx
// src/features/school/school-form.tsx:42
// ... existing imports/hooks ...
const handleSubmit = async () => {
  if (total < 0) return setError("ห้ามติดลบ"); // new
  await api.save(form);
};
// ... existing JSX ...
```

สั่ง "เช็ก lint กับ typecheck":

```
ไม่มี skill   yarn lint 2>&1 | tail -15; echo "=== TYPECHECK ==="; yarn typecheck 2>&1 | tail -25
             → log 34 บรรทัด แล้ว AI เรียกคำสั่งเพิ่มอีก 2 ครั้ง
มี skill      bash .../check.sh
             → ✅ fix · ✅ typecheck (163s)
```

## ผลทดสอบ

| ทดสอบ | ไม่มี skill | มี skill | ลดลง |
|---|---|---|---|
| AI อ่านภาพรวมโปรเจกต์ Next.js 319 ไฟล์ | 1,676.6k ตัวอักษร | 37.6k | **−98%** |
| AI อ่านภาพรวมโปรเจกต์ Vue 732 ไฟล์ | 9,150.2k ตัวอักษร | 114.8k | **−99%** |
| งานจริง: output ของคำสั่ง Bash ทั้งงาน | 38.0k ตัวอักษร | 5.6k | **−85%** |
| งานจริง: token รวมทั้งงาน | 2,186k | 1,837k | **−16%** |

งานจริง = โปรเจกต์ Next.js เดียวกัน 2 ชุด ส่งคำสั่งเดียวกัน (แก้ฟอร์ม, เช็ก lint, commit, ถามเรื่อง API, debug) ทั้งสองฝั่งตอบถูกเท่ากัน วิธีทดสอบและตัวเลขทั้งหมดอยู่ใน [tests/](tests/README.md)

## ข้อจำกัด

- ยุบตามรูปแบบของบรรทัด ไม่ได้ parse โค้ดจริง โค้ดแปลก ๆ อาจยุบไม่ครบ แต่ไม่ได้แก้ไฟล์ จึงไม่ทำให้โค้ดพัง
- กฎเป็นคำสั่งให้ AI ทำตาม ไม่ใช่การบังคับ บางครั้ง AI อาจกลับไปเขียนคำสั่งยาวเอง
- ไฟล์สั้น (~80 บรรทัด), JSON, `.env`, SQL AI จะอ่านตรง ๆ ไม่ผ่านตัวย่อ

## อ่านเพิ่ม

- [รายละเอียด](docs/details.md): อะไรถูกยุบบ้าง, กฎการตอบ, คำสั่งที่ใช้เองได้, ผลทดสอบแต่ละแบบ
- [SKILL.md](.claude/skills/bash-slim/SKILL.md): คำสั่งที่ AI ใช้จริง
