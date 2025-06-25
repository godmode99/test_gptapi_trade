# ภาพรวมการทำงานของระบบ

ไฟล์นี้สรุปขั้นตอนสำคัญของ workflow ตามแผนภาพใน `Work_flow_chart.png`
รายละเอียดเชิงลึกสามารถอ่านได้จาก [Work_flow.md](../Work_flow.md)
รวมถึงไฟล์ `live_trade/live_trade_flow.md` และ `back_test/backtest_flow.md`

1. **Fetch Data** – ดึงข้อมูล OHLC และคำนวณตัวชี้วัด (RSI, SMA, ATR) จาก MT5 หรือ
   yfinance แล้วบันทึกเป็น CSV และ JSON โดยสามารถเปิด/ปิดการคำนวณแต่ละค่าได้จากไฟล์คอนฟิก
2. **Send to GPT** – อ่านไฟล์ JSON และส่งคำสั่ง (prompt) ไปยัง GPT API เพื่อให้สร้างสัญญาณเทรด
3. **Parse Response** – แปลงข้อความที่ได้จาก GPT เป็น JSON และบันทึกลงไฟล์สัญญาณ
4. **EA ใน MT5** – อ่านไฟล์สัญญาณทุก ๆ รอบเวลา เพื่อนำไปเปิดคำสั่งซื้อขายจริงหรือตรวจสอบผลในโหมด Backtest

ลำดับการรันแบบอัตโนมัติสามารถตั้งเวลาได้ผ่าน `liveTrade_scheduler.py`
ซึ่งจะเรียก `live_trade_workflow.py` ตามช่วงเวลาที่ต้องการ
