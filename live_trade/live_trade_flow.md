📄 Live Trade Flow - GPT-Driven EA Signal System

1. เป้าหมายของ Live Trade Mode
   รันสัญญาณเทรดจริงแบบ Real-time ทุก 1 ชั่วโมง (หรือเวลาที่มึงตั้ง)

ใช้ GPT วิเคราะห์ข้อมูลราคาและ indicator ล่าสุด

ส่งสัญญาณเข้า EA ใน MT5 ให้ execute order อัตโนมัติ

Logging, monitoring, config เดียวคุมทุกอย่าง

2. High Level Flow (ตาม flowchart)
   pgsql
   คัดลอก
   แก้ไข
   [APScheduler]
   |
   [python main_liveTrade.py (entry point)]
   |
   [โหลด config]
   |
   [async flow]
   ├─ fetch mt5 timeserver + ohlcv
   ├─ calculate indicators (SMA, ATR, RSI)
   ├─ save fetch data as csv
   ├─ build prompt + call GPT API
   ├─ parse gpt response
   └─ save signals data as .csv & .json
   |
   [EA (MQL5) ฝั่ง MT5]
   ├─ readfile signals.csv ทุก 1 ชม.
   ├─ handle order & risk
   └─ live trade, export trade history
3. Step-by-Step Flow พร้อมอธิบายแต่ละขั้น
4. APScheduler: loop every 1 hr
   ตั้ง scheduler (เช่นรันใน VPS, server, หรือ PC บ้าน)

เรียก python live_trade/main_liveTrade.py ตาม interval ที่กำหนด (1 ชม. หรือแล้วแต่ config)

ข้อดี: ไม่ต้องเปิด script ค้างไว้, ไม่ต้องใช้ Task Scheduler แบบโบราณ

2. python live_trade/main_liveTrade.py (Entry Point)
   โหลด config (config/live.json หรือ path ที่ตั้งไว้)

กำหนด parameter ทั้งหมด: symbol, tf, bar, indicators, gpt model, output path ฯลฯ

3. async/await: main workflow
   3.1 fetch mt5 timeserver + ohlcv
   ดึงราคาสด (หรือใกล้เคียง real-time ที่สุด) จาก MT5 API/Bridge

sync เวลาให้ตรงกับ server/broker เพื่อกันเวลาเพี้ยน

3.2 calculate indicators (SMA, ATR, RSI)
คำนวณค่า indicators ตาม config

สามารถเพิ่ม/ลดได้ทันทีโดยเปลี่ยน config

3.3 save fetch data as csv file
Save ข้อมูล ohlcv + indicator ไว้ (debug/monitor/backtest)

ใช้เป็น input ของ prompt

3.4 call gpt api
รวม csv + prompt template

ส่งไปหา GPT (gpt-4o หรือ model ที่ตั้ง)

รอรับ signal กลับมา

3.5 send csv fetch file + prompt
Format prompt ให้ตรงกับ model, ตรวจสอบ input ให้ถูก

3.6 save file fetch + prompt text
Log ทั้ง data + prompt text เผื่อเอาไป debug ภายหลัง

ตรวจสอบได้ว่ารอบนี้ถามอะไรไป

3.7 parse gpt response
รับผลลัพธ์ GPT → extract JSON/object ของ signal

Validate รูปแบบข้อมูล เช่น entry, sl, tp, type

3.8 save signals data as .csv & .json file
บันทึก signal สำหรับรอบนั้นๆ

Save เป็น signals.csv (EA จะอ่าน) และอาจสำรองเป็น .json ด้วย

4. EA Integration Layer (ฝั่ง MQL5/MT5)
   4.1 EA: readfile signals.csv every 1 hour
   EA ฝั่ง MT5 จะเปิดไฟล์ signals.csv ทุกต้นชั่วโมงหรือ interval ที่กำหนด

ตรวจสอบว่า signal ใหม่หรือไม่

4.2 EA Function: HandleOrder & Risk Management
จัดการ order (pending, sl, tp)

วาง money/risk ตามระบบที่วางไว้

เช็กซ้ำกัน signal ซ้ำ/ข้ามเวลา/สัญญาณมั่ว

4.3 Live Trade: Execute EA Pending Order
ยิง order จริงเข้าตลาด

ถ้าไม่มี signal = ไม่เข้า order

4.4 Export Trade History
Log การเทรดจริงทุกครั้ง (ไว้ดู winrate, PnL, DD ฯลฯ)

export ได้เป็นไฟล์ .csv, .json หรือเข้า database ก็ได้

4. Key Output Files
   signals.csv (ไฟล์เดียวที่ EA ใช้)

ohlcv*fetch*{timestamp}.csv (ข้อมูลที่ส่งเข้า GPT, backup ไว้)

logs/run.log (monitor ว่าแต่ละรอบสำเร็จหรือ fail)

trades/live_trades.csv (บันทึก trade ที่เกิดขึ้นจริง)

5. เหตุผลที่ต้องออกแบบ Flow แบบนี้
   แยก logic AI (คิด signal) กับ EA (วาง order + คุม risk) อย่างชัดเจน

ทำงาน auto 100% ไม่ต้องมานั่งเฝ้า ไม่ต้องคลิกเอง

Debug ง่าย, ขยาย version/config/prompt/model ง่ายสุดๆ

Scale ไป backtest หรือ multi-symbol ได้ทันที

ปลอดภัย ถ้า GPT error → EA ไม่เข้า order (กันเทรดมั่ว)

6. ขยายต่อยอดได้ทันที
   เพิ่ม multi-symbol (แค่เพิ่ม config loop)

สลับ GPT model, เปลี่ยน prompt, เทสหลายชุดพร้อมกัน

เชื่อมต่อ Telegram/Line alert

สร้าง dashboard monitor ทุก signal/ทุกเทรด

7. ตัวอย่าง signals.csv
   c
   คัดลอก
   แก้ไข
   timestamp,entry,sl,tp,pending_order_type,confidence,comment
   2024-06-18 09:00,2320.5,2315.0,2335.0,buy_limit,91,"prompt_v2"
8. Logging & Monitoring
   ทุกครั้งที่ fetch, call gpt, parse, save signal ต้อง log status

ถ้า error/timeout จาก GPT → ต้อง log + alert admin

9. SOLID/Best Practice
   Core logic แยก module/folder: fetch, indicator, prompt, gpt, parse, signal_writer

ใช้ config file แทนแก้โค้ดตรงๆ

โค้ดพร้อม test + monitor + dev ใหม่ onboard สบาย
