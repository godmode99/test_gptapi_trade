# ตัวอย่างไฟล์ `config/setting_live_trade.example.json`

ไฟล์นี้เป็นเทมเพลตสำหรับโหมด Live Trade ก่อนใช้งานให้คัดลอกไปเป็นชื่อ `setting_live_trade.json` และแก้ไขค่าที่จำเป็น เช่น `openai_api_key` หรือข้อมูลการแจ้งเตือน

```bash
cp config/setting_live_trade.example.json config/setting_live_trade.json
```

## โครงสร้างหลัก

- **workflow** – ตั้งค่าชนิดตัวดึงข้อมูลและตำแหน่งสคริปต์ (`fetch`, `send`, `parse`)
- **fetch** – กำหนด `symbol`, `timeframes`, จำนวนแท่ง (`fetch_bars`) และการปรับเขตเวลา (`tz_shift`)
- **send** – ใส่คีย์ OpenAI และโมเดล GPT ที่ใช้
- **parse** – ตำแหน่งไฟล์ CSV/JSON ผลลัพธ์ที่แปลงแล้ว
- **signal_api** – URL, token และคีย์ `enabled` สำหรับส่งสัญญาณไป backend (ค่าเริ่มต้นเปิดใช้งาน)
- **neon** – ตัวอย่าง URL ฐานข้อมูล Neon และคีย์ `enabled` (ค่าเริ่มต้นเปิดใช้งาน)
- **risk_per_trade** / **max_risk_per_trade** – เปอร์เซ็นต์ความเสี่ยงต่อคำสั่ง
- **notify** – เปิดการแจ้งเตือนผ่าน LINE หรือ Telegram

รายละเอียดแต่ละคีย์อ่านได้ที่ [config_main_th.md](config_main_th.md)

หลังแก้ไขค่าต่าง ๆ แล้วสามารถรัน workflow ด้วยคำสั่ง

```bash
python src/gpt_trader/cli/live_trade_workflow.py
```

หรือระบุไฟล์คอนฟิกอื่นด้วย `--config` ตามต้องการ
