# คู่มือใช้งานระบบ Live Trade และ Backtest

เอกสารนี้สรุปขั้นตอนหลักในการใช้งานโครงการ ทั้งโหมด Live Trade และ Backtest
เพื่อให้ผู้ใช้ตั้งค่าระบบและรันสคริปต์ได้อย่างถูกต้อง

## 1. เตรียมสภาพแวดล้อม

1. ติดตั้งไลบรารีทั้งหมดตามไฟล์ `requirements.txt`
   ```bash
   ./scripts/install_deps.sh
   ```
2. สร้างไฟล์คอนฟิกจากตัวอย่างในโฟลเดอร์ `config/`
   - `setting_live_trade.example.json`
   - `setting_backtest.example.json`

   คัดลอกเป็นชื่อเดียวกันที่ตัดคำว่า `example` ออก แล้วแก้ไขค่า `openai_api_key`
   ให้เป็นคีย์ของคุณ

## 2. การรันโหมด Live Trade

1. ตรวจสอบไฟล์ `config/setting_live_trade.json` ว่ากำหนดค่าถูกต้องแล้ว
   สามารถระบุคีย์ `"risk_per_trade"` หรือ `"max_risk_per_trade"` เพื่อกำหนด
   ความเสี่ยงต่อการเทรด
   - `risk_per_trade` ใช้เป็นเปอร์เซ็นต์คงที่ หากตั้งค่าไว้จะนำไปใช้แทน
     ค่าในไฟล์สัญญาณ
   - `max_risk_per_trade` จะคำนวณจากค่าความมั่นใจของสัญญาณ โดยใช้สูตร
     `(confidence / 100) * max_risk_per_trade` และไม่เกินค่านี้
2. รันสคริปต์หลัก
   ```bash
   python main_liveTrade.py
   ```
   สามารถระบุอาร์กิวเมนต์เพิ่มเติมได้ เช่น `--config path/to/file.json`
   หรือ `--skip-fetch` เพื่อข้ามขั้นตอนดึงข้อมูล
3. สำหรับการรันแบบอัตโนมัติ ให้เรียก `src/gpt_trader/cli/liveTrade_scheduler.py`
   เพื่อทำงานทุกชั่วโมง สคริปต์นี้สามารถรันได้โดยตรง เพราะ
   `main_liveTrade.py` จะเพิ่ม path ของโปรเจกต์ให้อัตโนมัติ
   ```bash
   python src/gpt_trader/cli/liveTrade_scheduler.py
   ```

## 3. การรันโหมด Backtest

1. แก้ไขค่าต่าง ๆ ใน `config/setting_backtest.json` ให้ตรงกับช่วงเวลาที่ต้องการทดสอบ
2. เรียกสคริปต์
   ```bash
   python src/gpt_trader/cli/main_backtest.py --config config/setting_backtest.json
   ```
   สคริปต์จะดึงข้อมูลย้อนหลังทีละรอบตามที่กำหนดไว้ในไฟล์คอนฟิก แล้วบันทึกสัญญาณ
   ลงไฟล์ CSV ภายใต้ `data/back_test/signals/`

## 4. ตำแหน่งไฟล์สำคัญ

- ข้อมูลที่ดึงมาเก็บใน `data/*/fetch/`
- ไฟล์สัญญาณ CSV อยู่ใน `data/*/signals/signals_csv/`
- ไฟล์สัญญาณ JSON อยู่ใน `data/*/signals/signals_json/`
- สำเนา prompt และ JSON ที่ส่งให้ GPT จะถูกบันทึกเป็นไฟล์เดียวใน `data/*/save_prompt_api/`

ศึกษา flow รายละเอียดเพิ่มเติมได้ใน [Work_flow.md](../Work_flow.md)
และไฟล์ในโฟลเดอร์ `live_trade/docs/`
