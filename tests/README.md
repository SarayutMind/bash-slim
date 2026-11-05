# ทดสอบ bash-slim: AI ปกติ vs AI ที่มี skill

ทดสอบกับงานจริงในโปรเจกต์จริง แล้วดึงตัวเลขจาก log ของ Claude Code ไม่ได้ประมาณเอง

| ไฟล์ | คืออะไร |
|---|---|
| [prompt.txt](prompt.txt) | ข้อความที่ส่งให้ทั้งสองฝั่ง (เหมือนกันทุกตัวอักษร) |
| [ab.py](ab.py) | script ดึงตัวเลขจาก log 2 session แล้วพิมพ์ตารางเทียบ |
| [results/round1.md](results/round1.md) | ผลรอบ 1: ตัวเลขทั้งหมด + Bash/Read ทุกครั้งของทั้งสองฝั่ง |
| [results/round2.md](results/round2.md) | ผลรอบ 2 หลังแก้ skill 3 จุด |

## วิธีทดสอบ

1. clone โปรเจกต์ Next.js monorepo จริง (turbo, biome, husky + lint-staged, 6 packages) 2 ชุดจาก commit เดียวกัน ตัด remote ออก (push ไม่ได้) และไม่มี `.env` (ไม่แตะ database)
   - `test-normal`: ไม่มี skill
   - `test-skill`: มี `.claude/skills/bash-slim/` + กฎใน `CLAUDE.md` ที่ root (ซ่อนจาก git ด้วย `.git/info/exclude` ไม่ให้ติดไปตอน commit)
2. เปิด `claude` ในแต่ละโฟลเดอร์ ใช้ model เดียวกัน (Claude Opus 5.5) และ plugin ชุดเดียวกัน
3. วาง [prompt.txt](prompt.txt) ทั้งก้อนครั้งเดียวทั้งสองฝั่ง ข้อความมี 5 งาน:
   - แก้ฟอร์ม 1,294 บรรทัด ให้ช่องเว็บไซต์ต้องขึ้นต้นด้วย `http://` หรือ `https://`
   - เช็ก lint + typecheck
   - commit (มี husky + lint-staged)
   - ถามว่าหน้า `/manage/schools` อยู่ไฟล์ไหน เรียก API อะไร
   - debug error `fetch failed`
4. จบแล้วดึงตัวเลข:
   ```bash
   python tests/ab.py ~/.claude/projects/<normal-dir>/<session>.jsonl ~/.claude/projects/<skill-dir>/<session>.jsonl
   ```
5. ตรวจความถูกต้องเอง: ดู diff ของ commit ทั้งสองฝั่ง และเทียบคำตอบกับเฉลย

ก่อนรอบ 2: รีเซ็ตทั้งสองชุดกลับ commit เดิม ล้าง cache ของ typecheck (`.turbo`, `.next`, `tsbuildinfo`) และเช็กว่าไม่มี memory ค้างจากรอบ 1

`/context` กับ `/clear` ในข้อความถูกส่งเป็นตัวหนังสือ ไม่ได้รันเป็นคำสั่ง ทั้งสองฝั่งเหมือนกัน จึงไม่มีผลกับการเทียบ

## เฉลย

- **หน้า `/manage/schools`:** route `(pages)/(protected)/manage/schools/page.tsx` re-export จาก `features/manage-schools/page/manage-schools-page.tsx` เรียก API 9 ตัวผ่าน `manage-schools.actions.ts`: `GET /api/schools`, `/summary`, `/provinces`, `/areas`, `GET /api/projects`, `POST /api/schools/:id/status`, `POST /api/schools/:id/force-password-reset`, `GET /api/schools/:id/activities`, `DELETE /api/schools/:id`
- **`fetch failed`:** backoffice เรียก API ที่ `:4000` ไม่ถึง (API ไม่ได้รันหรือกำลัง restart) ไม่ใช่บัคในบรรทัดนั้น

## ผล

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
| แก้โค้ดถูก (เช็กทั้งฟอร์มและ API) | ถูก | ถูก | ถูก | ถูก | เท่ากัน |
| API ที่ตอบได้ (จาก 9) | 8 | 8 | 9 | 9 | เท่ากัน |
| debug `fetch failed` | ถูก | ถูก | ถูก | ถูก | เท่ากัน |
| ภาษาของคำตอบ | ไทย | อังกฤษ | อังกฤษ | ไทย | |

## สิ่งที่เจอในรอบ 1 และแก้ก่อนรอบ 2

| ปัญหา | แก้ | รอบ 2 |
|---|---|---|
| ภาพรวมโฟลเดอร์ 30 ไฟล์ได้ 24.9k ตัวอักษรก้อนเดียว ทำให้ output ของ Bash ฝั่ง skill มากกว่าฝั่งปกติ (+24%) | ไฟล์ละบรรทัด + ใช้ `Grep` ก่อน | 4.1k, Bash OUT −85% |
| lint ทั้ง repo พังเพราะ CRLF, `check.sh` โชว์ diff 40 บรรทัด AI เรียก Bash เพิ่มอีก 3 ครั้ง | จัดกลุ่ม error, โชว์ `Found N errors`, บอกว่าเป็น CRLF และไม่ใช่ไฟล์ที่แก้ | AI lint เฉพาะไฟล์ที่แก้ ผ่านใน 1 บรรทัด |
| ฝั่ง skill ตอบเป็นภาษาอังกฤษ | กฎ "ตอบภาษาเดียวกับผู้ใช้" | ตอบไทย |

## ข้อควรรู้

- **รอบ 2 ฝั่ง skill เสียเปรียบ:** session ฝั่ง skill โหลด `CLAUDE.md` ของ `apps/backoffice` และ `apps/api` (36.6k ตัวอักษร ≈ 15k token) เข้ามาเองระหว่างทำงาน และติดอยู่ใน 18 จาก 23 รอบ ฝั่งปกติไม่โหลด (log ฝั่ง skill มี path แบบ `/c/Users`, ฝั่งปกติเป็น `C:\Users` น่าจะเปิด terminal คนละแบบ) ถ้าหักออก token รวมลดราว −28% ดูได้จากแถว "CLAUDE.md ย่อยที่โหลดระหว่างทำงาน" ใน [results/round2.md](results/round2.md)
- **รอบ 2 lint คนละแบบ:** ฝั่ง skill lint เฉพาะไฟล์ที่แก้ (`check.sh` ค่าเริ่มต้น) ฝั่งปกติ lint ทั้ง repo แล้วเจอ error CRLF 444 ตัวที่มีอยู่เดิม ไม่เกี่ยวกับงานนี้
- **plugin ย่อคำตอบ (caveman) เปิดทั้งสองฝั่ง** ความยาวคำตอบเลยต่างกันไม่มาก
- **รันรอบละครั้งต่อฝั่ง** AI ทำงานไม่เหมือนเดิมทุกครั้ง ตัวเลขจึงขยับได้
- **token รวมยังห่างเป้า 75%** เพราะ token ส่วนใหญ่คือ context พื้นฐานของ Claude Code (~48k ตั้งแต่เริ่ม) กับโค้ดที่จำเป็นต้องอ่าน skill ลดได้มากที่ส่วน Bash
- **ไม่ได้เก็บ log ดิบกับ diff โค้ด** ไว้ใน repo เพราะ log มีข้อมูลของเครื่องและ system prompt ส่วนโค้ดเป็นของโปรเจกต์บริษัท
