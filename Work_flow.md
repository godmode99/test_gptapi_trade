📄 AI Trading System – Flow Chart Documentation

1. System Overview
   เอกสารนี้อธิบายโครงสร้างและการทำงานของระบบ AI Trading (Auto Signal & Execution) ที่ใช้ GPT API วิเคราะห์กราฟจาก MT5 แล้วส่งคำสั่งเทรดแบบอัตโนมัติ พร้อม Risk Management

2. Flow Chart Diagram
   (แนบไฟล์ภาพ flow chart นี้ในเอกสาร)
   เช่น
   ไฟล์ภาพ Work_flow_chart.png
   [แทรกภาพ flow chart]
3. Step-by-Step Description
   3.1 MT5: OHLCV, RSI14, SMA20, ATR14
   ดึงข้อมูลกราฟ (OHLCV) และค่า indicator (RSI, SMA, ATR) หลาย timeframe จาก MT5

รองรับ multi-timeframe analysis

3.2 Python: Fetch multi-timeframe data & save as CSV
สคริปต์ Python ดึงข้อมูลจาก MT5 หลาย TF

แปลงข้อมูลเป็นไฟล์ .CSV พร้อม export indicator

3.3 Python: Send CSV + prompt to GPT API
Python script ส่งไฟล์ CSV + คำสั่ง (prompt) ไป GPT API (OpenAI)

อธิบาย logic ที่อยากให้ AI วิเคราะห์ เช่น ขอ entry/sl/tp/position

3.4 GPT Output (Raw Response)
AI วิเคราะห์ข้อมูลและตอบกลับเป็น text หรือ JSON

ตัวอย่างผลลัพธ์:

json
{
"signal_id": "xauusd-20250616_14hr",
"entry": 12,
"sl": 10,
"tp": 20,
"pending_order_type": "buy_limit",
"confidence": 77
}

3.5 Parse response to JSON file & save to folder
แปลงข้อความจาก GPT เป็น JSON

บันทึกแยกไฟล์/โฟลเดอร์ตามรอบ หรือ signal_id

3.6 n8n: Loop automate fetch & signal process every 1 hour
Workflow อัตโนมัติ (ใช้ n8n หรือ cronjob)

ทำซ้ำทุก 1 ชั่วโมง: ดึงข้อมูล → ส่ง AI → เก็บผลลัพธ์

3.7 EA: Read JSON signal every 1 hour
EA (Expert Advisor) อ่านไฟล์ JSON ที่มีสัญญาณใหม่ทุกชั่วโมง

3.8 EA Function: HandleOrder & Risk Management
EA คำนวณ position size ตาม risk (หรือ logic ที่ตั้งไว้)

สั่งเปิด pending order หรือ market order ตามสัญญาณ

3.9 Live Trade: Execute EA Pending Order
ส่ง order เข้า MT5 live account

4. Key Features
   Multi-timeframe analysis

AI signal generation (GPT)

Auto execution (EA + MM)

Confidence scoring

Export history, optimize & backtest ง่าย

Modular, debug/ปรับปรุงทุกจุดได้

5. Error Handling & Logging (แนะนำให้เพิ่ม)
   Log ทุกจุด: fetch fail, API error, EA fail

(option) Alert via line/telegram

6. Example JSON Signal Structure
   json
   {
   "signal_id": "xauusd-20250616_14hr",
   "entry": 2332.14,
   "sl": 2327.50,
   "tp": 2340.50,
   "pending_order_type": "buy_limit",
   "confidence": 81
   }
หมายเหตุ:
- pending_order_type เลือกได้จาก [buy_limit, sell_limit, buy_stop, sell_stop]
- confidence แสดงเป็นเปอร์เซ็นต์ช่วง 1-100%

7. Extensibility
   เพิ่ม simulation/backtest ได้

รองรับปรับ logic, indicator, prompt ได้ตลอดเวลา
