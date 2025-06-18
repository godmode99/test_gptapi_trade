📄 Backtest Flow - GPT-Driven EA Signal System

1. วัตถุประสงค์ของ Backtest Mode
   ทดสอบความแม่นของ signal ที่ GPT คิดจากข้อมูลย้อนหลัง

วัด performance ของ AI strategy กับ historical data จริง

ใช้ EA ฝั่ง MT5 จำลองเทรดตาม signal เพื่อหาจุดอ่อนจุดแข็งของระบบ

2. Overview Flow (จากแผนภาพ/flowchart)
   pgsql
   คัดลอก
   แก้ไข
   [Config File]
   |
   [main.py (Entry)]
   |
   [Start Loop: from start_time to end_time, step = n hr]
   |
   [แต่ละรอบเวลา:]
   ├─ fetch mt5 ohlcv + sync time
   ├─ calculate indicators (SMA, ATR, RSI)
   ├─ save fetch data as csv
   ├─ build prompt + call GPT API
   ├─ parse response → signal
   └─ append signal ลง table (backtest_signals.csv)
   |
   [จบรอบ → เพิ่มเวลา → วน loop]
   |
   [ครบ end_time → stop]
   |
   [EA (MQL5) อ่าน backtest_signals.csv]
   |
   [Backtest ใน MT5, Export Trade History]
3. Step-by-Step Flow พร้อมอธิบายแต่ละขั้น
4. เตรียม config
   ไฟล์ backtest.json ต้องระบุ:

symbol, timeframe

start_time, end_time

interval (loop ทุกกี่นาที/ชั่วโมง)

indicator ที่ต้องการใช้

path ของ signal table output

ตัวอย่าง config:

json
คัดลอก
แก้ไข
{
"symbol": "XAUUSD",
"timeframe": "M15",
"start_time": "2024-01-01 00:00:00",
"end_time": "2024-03-01 00:00:00",
"loop_every_minutes": 60,
"indicators": ["SMA20", "ATR14", "RSI14"],
"gpt_model": "gpt-4o",
"prompt_template": "prompts/backtest_prompt.txt",
"signal_table": "signals/backtest/backtest_signals.csv"
} 2. main.py: Entry Point
โหลด config

set ค่าเริ่มต้น, สร้าง signal table ถ้ายังไม่มี

3. Start Loop
   เริ่มจาก now = start_time

วนไปจนถึง now > end_time

ในแต่ละรอบของเวลา:

3.1 Fetch mt5 timeserver + ohlcv
ดึงราคาย้อนหลังจาก MT5 หรือ Data Source (API, CSV)

sync เวลาให้ตรงกับ timestamp ของ loop รอบนั้น

3.2 Calculate Indicators
คำนวณ SMA, ATR, RSI จาก ohlcv ชุดนั้น

3.3 Save fetch data as csv file
สำรอง raw data & indicator ในแต่ละรอบ

ไว้ debug และตรวจสอบย้อนหลัง

3.4 Call GPT API
สร้าง prompt จาก template + ใส่ csv data (ohlcv+indicator)

ส่งไปที่ GPT API (openai/gpt-4o)

รอรับ response กลับมา

3.5 Parse GPT Response
ดึง JSON หรือ signal structure ออกจาก response

ตัวอย่างที่คาดหวัง:

json
คัดลอก
แก้ไข
{
"timestamp": "2024-01-01 09:00",
"entry": 2320.5,
"sl": 2312.0,
"tp": 2335.0,
"pending_order_type": "buy_limit",
"confidence": 85
}
3.6 Add signal ลง table
append signal ที่ได้ลง backtest_signals.csv

1 row = 1 รอบเวลา (timestamp)

4. End 1 loop
   เพิ่มเวลาต่อไป (now = now + interval)

วนกลับไป step 3 จนกว่าจะถึง end_time

5. stop at end_time
   จบ process backtest (ปิดไฟล์, export summary, log ผล)

6. EA: readfile backtest_signals.csv
   EA ฝั่ง MT5 จะ load ข้อมูล signal table นี้

จำลองคำสั่งเทรดตาม signal ทีละรอบเวลา

ตั้ง SL/TP ตามที่ model/gpt คิดมา

7. Back test in MT5
   MT5 จำลอง market + ยิง order ตามสัญญาณ

สรุปผลกำไร/ขาดทุน, drawdown, winrate ฯลฯ

8. Export Trade History
   EA หรือ MT5 export ไฟล์สรุปการเทรดทั้งหมด

ข้อมูลที่ได้ใช้สำหรับวิเคราะห์ประสิทธิภาพ model/strategy

4. Key Output File/Format
   backtest_signals.csv

pgsql
คัดลอก
แก้ไข
timestamp,entry,sl,tp,pending_order_type,confidence,strategy_id,comment
2024-01-01 09:00,2320.5,2312.0,2335.0,buy_limit,85,gpt4o_v1,"test"
mt5_trade_history.csv

sql
คัดลอก
แก้ไข
timestamp,order_id,entry,sl,tp,result,strategy_id 5. เหตุผลที่วาง Flow แบบนี้
ทุก signal มีที่มา สามารถ debug ได้ย้อนกลับทุก loop

GPT เป็นแค่ “สมอง” ส่วน Logic + Risk อยู่ที่ EA (ควบคุมได้)

โครงสร้างแยกชัด → เทสหลาย model ได้ง่าย

สามารถ automate backtest ได้ 100% (ไม่ต้องคลิกทีละรอบ)

ถ้าเปลี่ยน config → ไม่ต้องแก้โค้ดเลย

6. จุดที่ควรระวัง
   ต้อง validate response ของ GPT ทุกครั้ง (กัน error/มั่ว)

ต้อง backup ข้อมูล fetch/raw data เพื่อ audit

อย่าลืมตั้ง timezone/timestamp ให้ตรงกับตลาดจริง

7. ข้อได้เปรียบ
   เทียบ performance ได้ทุก version

วัดจุดเข้า/SL/TP ว่า “สั่งโดย AI” มันแม่นจริงมั้ย

เตรียมเทส logic EA ได้ง่ายสุดๆ

8. สามารถขยาย/ปรับแต่งได้
   Multi-symbol/multi-timeframe backtest

ลอง model อื่นหรือ GPT prompt version อื่นได้ทันที

ต่อ automation ทำ parameter optimization loop ก็ยังได้
