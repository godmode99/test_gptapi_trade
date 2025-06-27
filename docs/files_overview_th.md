# สรุปรายการไฟล์ในโครงการ

เอกสารนี้อธิบายหน้าที่โดยย่อของไฟล์และโฟลเดอร์หลัก ๆ ภายในรีโป
เพื่อให้ผู้ใช้งานเข้าใจโครงสร้างโดยรวม

## โฟลเดอร์ระดับบนสุด

| เส้นทาง | คำอธิบาย |
|---------|-----------|
| `src/` | โค้ดไพธอนของระบบหลัก แบ่งเป็นโมดูลย่อย |
| `config/` | ไฟล์ตัวอย่างสำหรับตั้งค่าการทำงานทั้ง Live Trade และ Backtest |
| `live_trade/` | โฟลเดอร์สำหรับข้อมูลและเอกสารของโหมด Live Trade |
| `back_test/` | ตัวอย่างคอนฟิกและเอกสารการทำงานในโหมด Backtest |
| `data/` | ที่เก็บผลลัพธ์ต่าง ๆ เช่น CSV/JSON |
| `scripts/` | สคริปต์ช่วยเหลือ เช่น ติดตั้งไลบรารี |
| `tests/` | ชุดทดสอบอัตโนมัติ |
| `backend/` | รวมซอร์สโค้ด API หลายเวอร์ชัน<br>├─ `api/` JavaScript เชื่อมต่อ Supabase<br>├─ `neon-ts/` TypeScript ใช้ฐานข้อมูล Neon<br>└─ `supabase/` ไฟล์ `schema.sql` |

## โมดูล `src/gpt_trader`

| เส้นทาง | หน้าที่ |
|---------|---------|
| `cli/` | สคริปต์ command line สำหรับรัน workflow |
| `fetch/` | ฟังก์ชันดึงข้อมูลราคาจาก MT5 หรือ Yahoo Finance |
| `send/` | โมดูลเรียก GPT API จาก JSON ที่เตรียมไว้ |
| `parse/` | แปลงผลลัพธ์ที่ได้จาก GPT เป็นรูปแบบที่ EA ใช้งานได้ |
| `utils/` | ฟังก์ชันช่วย เช่น การคำนวณ indicator |

-### รายละเอียดสคริปต์สำคัญ

- `cli/live_trade_workflow.py` — รันขั้นตอน fetch → send → parse ตามค่าคอนฟิก
- `cli/main_backtest.py` — รันการทดสอบย้อนหลังตามช่วงเวลาในคอนฟิก
- `cli/liveTrade_scheduler.py` — ตัวอย่างตั้งเวลาเรียก `live_trade_workflow.py`
- `fetch/fetch_mt5_data.py` — ดึงข้อมูลราคาและคำนวณ indicator ผ่าน MT5
- `fetch/fetch_yf_data.py` — ดึงข้อมูลจาก yfinance
- `send/send_to_gpt.py` — ส่งข้อมูลไป GPT และบันทึกสำเนา prompt
- `parse/parse_gpt_response.py` — แปลงข้อความตอบกลับเป็นไฟล์สัญญาณ

## โฟลเดอร์ `live_trade`

ภายในเก็บไฟล์ที่เกี่ยวข้องกับการเทรดจริง เช่น

- `live_trade_flow.md` — อธิบายขั้นตอนการทำงานแบบละเอียด
- `docs/` — คู่มือภาษาไทยสำหรับการตั้งค่าและเรียกใช้งาน
- `data/` — เก็บ CSV/JSON ที่สร้างในโหมด Live Trade
- `ea/` — โค้ด MQL5 สำหรับอ่านสัญญาณและแสดงผลใน MT5

## โฟลเดอร์ `back_test`

- `backtest_flow.md` — คำอธิบายลำดับการทำงานโหมด Backtest
- `backtest.json` — ตัวอย่างคอนฟิกสำหรับการรัน backtest

เอกสาร flow หลักสามารถดูเพิ่มเติมได้ใน [Work_flow.md](Work_flow.md)
