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

สคริปต์ `live_trade_workflow.py` จะเรียกขั้นตอน fetch → send → parse ตามค่าที่กำหนดใน `setting_live_trade.json`

```bash
python src/gpt_trader/cli/live_trade_workflow.py
```

สามารถกำหนดอาร์กิวเมนต์เพิ่มเติมได้ เช่น

- `--config PATH` ใช้ไฟล์คอนฟิกอื่นแทนค่าเริ่มต้น
- `--fetch-type mt5|yf` เลือกตัวดึงข้อมูล
- `--skip-fetch`, `--skip-send`, `--skip-parse` ข้ามบางขั้นตอน

ตัวอย่างรันโดยใช้ไฟล์คอนฟิกอื่นและข้ามการดึงข้อมูล

```bash
python src/gpt_trader/cli/live_trade_workflow.py --config my_config.json --skip-fetch
```

## การรันแบบอัตโนมัติ

ใช้สคริปต์ `src/gpt_trader/cli/liveTrade_scheduler.py` เพื่อเรียก `live_trade_workflow.py` ทุก ๆ ชั่วโมง

```bash
python src/gpt_trader/cli/liveTrade_scheduler.py
```

กด **Ctrl+C** เพื่อหยุดการทำงานของ scheduler

## การแจ้งเตือนผลการรัน

หากกำหนด `notify` และเปิด `line.enabled` หรือ `telegram.enabled` ระบบจะส่งสรุปผลการรัน
ผ่าน LINE หรือ Telegram ตามค่า token และ chat_id ในแต่ละส่วน
นอกจากนี้ไฟล์ `logs/run.log` จะบันทึกข้อความแจ้งเตือนทุกครั้งที่มีการส่ง LINE หรือ Telegram
ข้อความที่ส่งจะแสดงรายละเอียดสัญญาณ รวมถึงค่า `risk_per_trade` ที่ใช้เปิดออเดอร์
เพื่อให้ผู้อ่านเห็นเปอร์เซ็นต์ความเสี่ยงของคำสั่งแต่ละครั้งอย่างชัดเจน
