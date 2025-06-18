# คู่มือการใช้งาน `config/setting_live_trade.json`

ไฟล์ `config/setting_live_trade.json` ใช้กำหนดค่าสำหรับรันสคริปต์ `main_liveTrade.py` ซึ่งทำหน้าที่
เรียกขั้นตอนการดึงข้อมูล ส่งข้อมูลไป GPT และแปลงผลลัพธ์เป็นไฟล์สัญญาณ
โดยสามารถปรับแต่งค่าต่าง ๆ ได้ดังนี้

โครงสร้างไฟล์แบ่งออกเป็นหมวดหมู่ดังนี้

| หมวด | คีย์ย่อย | คำอธิบาย |
|------|---------|-----------|
| `workflow.fetch_type` |  | กำหนดประเภทตัวดึงข้อมูลอัตโนมัติ (`yf` หรือ `mt5`) |
| `workflow.scripts.fetch` |  | พาธสคริปต์ดึงข้อมูล (ไม่ระบุเพื่อใช้ตัวในระบบ) |
| `workflow.scripts.send` |  | พาธสคริปต์ส่งข้อมูลไป GPT |
| `workflow.scripts.parse` |  | พาธสคริปต์แปลงผลลัพธ์จาก GPT |
| `workflow.response` |  | ไฟล์เก็บข้อความตอบกลับดิบจาก GPT |
| `workflow.skip.fetch` |  | ตั้งค่า `true` เพื่อข้ามขั้นตอนดึงข้อมูล |
| `workflow.skip.send` |  | ตั้งค่า `true` เพื่อข้ามการส่งข้อมูล |
| `workflow.skip.parse` |  | ตั้งค่า `true` เพื่อข้ามการแปลงผลลัพธ์ |
| `fetch` |  | คอนฟิกสำหรับขั้นตอนดึงข้อมูล |
| `send` |  | คอนฟิกสำหรับขั้นตอนส่งข้อมูลไป GPT |
| `parse` |  | คอนฟิกสำหรับขั้นตอนแปลงผลลัพธ์ |

ตัวอย่างโครงสร้างไฟล์:

```json
{
  "workflow": {
    "fetch_type": "mt5",
    "scripts": {
      "fetch": null,
      "send": "scripts/send_api/send_to_gpt.py",
      "parse": "scripts/parse_response/parse_gpt_response.py"
    },
    "response": "data/live_trade/signals/latest_response.txt",
    "skip": {"fetch": false, "send": false, "parse": false}
  },
  "fetch": {
    "symbol": "XAUUSD"
  },
  "send": {
    "openai_api_key": "YOUR_API_KEY"
  },
  "parse": {
    "tz_shift": 7
  }
}
```

เมื่อใช้ `main_liveTrade.py` หากไม่ส่งอาร์กิวเมนต์ `--config` โปรแกรมจะอ่านค่าในไฟล์นี้
อัตโนมัติ สามารถแก้ไขค่าหรือระบุไฟล์อื่นผ่าน `--config` ได้
และยังสามารถกำหนดอาร์กิวเมนต์บนคำสั่งเพื่อ override ค่าจากไฟล์นี้อีกชั้นหนึ่ง

ตัวอย่างรันโดยใช้การตั้งค่าในไฟล์:

```bash
python live_trade/main_liveTrade.py
```

หรือใช้ไฟล์คอนฟิกอื่น:

```bash
python live_trade/main_liveTrade.py --config path/to/other.json
```

สามารถเลือกข้ามบางขั้นตอนด้วยอาร์กิวเมนต์ เช่น

```bash
python live_trade/main_liveTrade.py --skip-fetch --skip-send
```

เพื่อทดสอบเพียงขั้นตอน parse เป็นต้น

