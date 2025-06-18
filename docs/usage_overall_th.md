# คู่มือใช้งานระบบ Live Trade และ Backtest

เอกสารนี้สรุปขั้นตอนหลักในการใช้งานโครงการ ทั้งโหมด Live Trade และ Backtest
เพื่อให้ผู้ใช้ตั้งค่าระบบและรันสคริปต์ได้อย่างถูกต้อง

## 1. เตรียมสภาพแวดล้อม

1. ติดตั้งไลบรารีทั้งหมดตามไฟล์ `requirements.txt` และติดตั้งแพ็กเกจ
   ```bash
   ./scripts/install_deps.sh
   pip install -e .
   ```
2. สร้างไฟล์คอนฟิกจากตัวอย่างในโฟลเดอร์ `config/`
   - `setting_live_trade.example.json`
   - `setting_backtest.example.json`

   คัดลอกเป็นชื่อเดียวกันที่ตัดคำว่า `example` ออก แล้วแก้ไขค่า `openai_api_key`
   ให้เป็นคีย์ของคุณ

## 2. การรันโหมด Live Trade

1. ตรวจสอบไฟล์ `config/setting_live_trade.json` ว่ากำหนดค่าถูกต้องแล้ว
2. รันสคริปต์หลัก
   ```bash
   python -m gpt_trader.cli.main_liveTrade
   ```
   สามารถระบุอาร์กิวเมนต์เพิ่มเติมได้ เช่น `--config path/to/file.json`
   หรือ `--skip-fetch` เพื่อข้ามขั้นตอนดึงข้อมูล
3. สำหรับการรันแบบอัตโนมัติ ให้เรียก `src/gpt_trader/cli/scheduler_example.py`
   เพื่อทำงานทุกชั่วโมง
   ```bash
   python src/gpt_trader/cli/scheduler_example.py
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
- สำเนา prompt และ CSV ที่ส่งให้ GPT จะอยู่ใน `data/*/save_prompt_api/`

ศึกษา flow รายละเอียดเพิ่มเติมได้ใน [Work_flow.md](../Work_flow.md)
และไฟล์ในโฟลเดอร์ `live_trade/docs/`
