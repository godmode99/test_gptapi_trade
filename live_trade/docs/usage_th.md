# วิธีใช้งานระบบเทรด (ภาษาไทย)

เอกสารนี้อธิบายขั้นตอนการเตรียมระบบและคำสั่งพื้นฐานสำหรับรัน workflow อัตโนมัติ
โดยใช้ไฟล์ตัวอย่างและสคริปต์ที่มีในโปรเจกต์

## ติดตั้งไลบรารีที่จำเป็น

รันสคริปต์ `scripts/install_deps.sh` เพื่อดาวน์โหลดและติดตั้งไลบรารีทั้งหมดจาก `requirements.txt`

```bash
./scripts/install_deps.sh
```

## สร้างไฟล์ตั้งค่า `setting_live_trade.json`

โปรเจกต์มีเทมเพลต `config/setting_live_trade.example.json` อยู่แล้ว
คัดลอกไฟล์นี้เป็น `setting_live_trade.json` แล้วแก้ไขค่า `openai_api_key`

```bash
cp config/setting_live_trade.example.json \
   config/setting_live_trade.json
# แก้ไขค่าคีย์ให้เป็น API key ของคุณ
```

## รันสคริปต์หลัก

สคริปต์ `main_liveTrade.py` จะเรียกขั้นตอน fetch → send → parse ตามค่าที่กำหนดใน `setting_live_trade.json`

```bash
python main_liveTrade.py
```

สามารถกำหนดอาร์กิวเมนต์เพิ่มเติมได้ เช่น

- `--config PATH` ใช้ไฟล์คอนฟิกอื่นแทนค่าเริ่มต้น
- `--fetch-type mt5|yf` เลือกตัวดึงข้อมูล
- `--skip-fetch`, `--skip-send`, `--skip-parse` ข้ามบางขั้นตอน

ตัวอย่างรันโดยใช้ไฟล์คอนฟิกอื่นและข้ามการดึงข้อมูล

```bash
python main_liveTrade.py --config my_config.json --skip-fetch
```

## การรันแบบอัตโนมัติ

ใช้สคริปต์ `src/gpt_trader/cli/liveTrade_scheduler.py` เพื่อเรียก `main_liveTrade.py` ทุก ๆ ชั่วโมง

```bash
python src/gpt_trader/cli/liveTrade_scheduler.py
```

กด **Ctrl+C** เพื่อหยุดการทำงานของ scheduler

## การแจ้งเตือนผลการรัน

หากกำหนด `notify` และเปิด `line.enabled` หรือ `telegram.enabled` ระบบจะส่งสรุปผลการรัน
ผ่าน LINE หรือ Telegram ตามค่า token และ chat_id ในแต่ละส่วน
