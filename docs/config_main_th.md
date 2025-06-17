# คู่มือการใช้งาน `config/main.json`

ไฟล์ `config/main.json` ใช้กำหนดค่าสำหรับรันสคริปต์ `main.py` ซึ่งทำหน้าที่
เรียกขั้นตอนการดึงข้อมูล ส่งข้อมูลไป GPT และแปลงผลลัพธ์เป็นไฟล์สัญญาณ
โดยสามารถปรับแต่งค่าต่าง ๆ ได้ดังนี้

| คีย์ | คำอธิบาย |
|------|-----------|
| `fetch_type` | กำหนดประเภทตัวดึงข้อมูลอัตโนมัติ ระบุ `yf` (Yahoo Finance) หรือ `mt5` |
| `fetch_script` | พาธไปยังสคริปต์ดึงข้อมูลเอง หากระบุค่านี้จะไม่ใช้ `fetch_type` |
| `send_script` | พาธสคริปต์ส่งข้อมูลไปยัง GPT API |
| `parse_script` | พาธสคริปต์แปลงผลลัพธ์จาก GPT |
| `response` | ไฟล์เก็บข้อความตอบกลับดิบจาก GPT ชั่วคราว |
| `skip_fetch` | ตั้งค่าเป็น `true` เพื่อข้ามขั้นตอนดึงข้อมูล |
| `skip_send` | ตั้งค่าเป็น `true` เพื่อข้ามการส่งข้อมูลไป GPT |
| `skip_parse` | ตั้งค่าเป็น `true` เพื่อข้ามการแปลงผลลัพธ์ |

ตัวอย่างเนื้อหาเริ่มต้นในไฟล์มีดังนี้:

```json
{
  "fetch_type": "yf",
  "fetch_script": null,
  "send_script": "scripts/send_api/send_to_gpt.py",
  "parse_script": "scripts/parse_response/parse_gpt_response.py",
  "response": "data/signals/latest_response.txt",
  "skip_fetch": false,
  "skip_send": false,
  "skip_parse": false
}
```

เมื่อใช้ `main.py` หากไม่ส่งอาร์กิวเมนต์ `--config` โปรแกรมจะอ่านค่าในไฟล์นี้
อัตโนมัติ สามารถแก้ไขค่าหรือระบุไฟล์อื่นผ่าน `--config` ได้
และยังสามารถกำหนดอาร์กิวเมนต์บนคำสั่งเพื่อ override ค่าจากไฟล์นี้อีกชั้นหนึ่ง

ตัวอย่างรันโดยใช้การตั้งค่าในไฟล์:

```bash
python main.py
```

หรือใช้ไฟล์คอนฟิกอื่น:

```bash
python main.py --config path/to/other.json
```

สามารถเลือกข้ามบางขั้นตอนด้วยอาร์กิวเมนต์ เช่น

```bash
python main.py --skip-fetch --skip-send
```

เพื่อทดสอบเพียงขั้นตอน parse เป็นต้น

