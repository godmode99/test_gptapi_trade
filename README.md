# ระบบเทรดอัตโนมัติ (AI Trading System)

โปรเจ็กต์นี้รวบรวมขั้นตอนดึงข้อมูลกราฟจาก MT5 หรือ yfinance ส่งให้ GPT วิเคราะห์และแปลงผลลัพธ์เป็นไฟล์สัญญาณเพื่อใช้เปิดออเดอร์อัตโนมัติ รายละเอียดการทำงานดูได้ที่ [docs/Work_flow.md](docs/Work_flow.md)

## สารบัญ

- [การติดตั้ง](#การติดตั้ง)
- [โครงสร้างไดเรกทอรี](#โครงสร้างไดเรกทอรี)
- [การตั้งค่า](#การตั้งค่า)
- [รัน workflow](#รัน-workflow)
- [Backtesting](#backtesting)
- [Backend API](#backend-api)
- [CustomIndicator](#customindicator)
- [การทดสอบ](#การทดสอบ)
- [การแก้ปัญหา](#การแก้ปัญหา)

## การติดตั้ง

ติดตั้งไลบรารีทั้งหมดตาม `requirements.txt` ด้วยสคริปต์

```bash
./scripts/install_deps.sh
```

### ติดตั้ง MetaTrader5

1. ดาวน์โหลด MetaTrader 5 และติดตั้งให้ตรงกับสถาปัตยกรรม Python (ส่วนใหญ่ 64 บิต)
2. หาก `mt5.initialize()` ไม่พบโปรแกรมอัตโนมัติ ให้ระบุ path เอง เช่น

```python
mt5.initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe")
```

บน Linux ที่ใช้ Wine path จะเป็น `~/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe`

### ตั้งค่า OpenAI API key

คัดลอกไฟล์ตัวอย่างและแก้ไขค่า

```bash
cp src/gpt_trader/send/config/gpt.example.json src/gpt_trader/send/config/gpt.json
```

เปิด `gpt.json` เพื่อใส่ `openai_api_key` ของคุณ

## โครงสร้างไดเรกทอรี

- `data/live_trade/` – เก็บ CSV และ JSON ที่สร้างจากการรัน
  - `fetch/` – ข้อมูลราคาที่ดึงมา
  - `signals/signals_json/` – ไฟล์สัญญาณรูปแบบ JSON
  - `signals/signals_csv/` – บันทึกผลการ parse เป็น CSV
- `src/gpt_trader/` – โค้ดหลักของระบบ
- `ea/` – โค้ดสำหรับใช้งานใน MT5
- `logs/` – ไฟล์บันทึกการทำงาน

## มาตรฐานการเขียนโค้ด

โค้ดในโปรเจ็กต์นี้แยกส่วน Input/Output ออกจาก business logic อ่านรายละเอียดได้ที่ [CODE_STANDARD.md](CODE_STANDARD.md)

## การตั้งค่า

สคริปต์ `fetch_mt5_data.py` อ่านค่าจาก `src/gpt_trader/fetch/config/fetch_mt5.json` สามารถกำหนดไฟล์อื่นด้วย `--config`
ตัวอย่างคีย์ที่ใช้ได้ได้แก่ `symbol`, `fetch_bars`, `indicators`, `time_fetch`, `timeframes` และ `tz_shift`
สำหรับบันทึกประวัติการเทรดใช้ `fetch_mt5_history.py` โดยกำหนดช่วงเวลาใน `src/gpt_trader/fetch/config/fetch_mt5_history.json`

เมื่อรัน `live_trade_workflow.py` ให้สร้างไฟล์ `config/setting_live_trade.json` จากเทมเพลต

```bash
cp config/setting_live_trade.example.json config/setting_live_trade.json
```

ใส่ค่า `openai_api_key` และปรับคีย์อื่นตามต้องการ รายละเอียดคีย์ดูที่ [live_trade/docs/config_main_th.md](live_trade/docs/config_main_th.md)

## รัน workflow

หลังตั้งค่าแล้วสามารถรันทั้งกระบวนการได้ด้วย

```bash
python src/gpt_trader/cli/live_trade_workflow.py
```

ใช้ `--config` เพื่อระบุไฟล์คอนฟิกอื่น หรือ `--skip-fetch` `--skip-send` `--skip-parse` เพื่อข้ามบางขั้นตอน นอกจากนี้ยังมี `src/gpt_trader/cli/scheduler_liveTrade.py` สำหรับรันตามเวลาที่กำหนด

## Backtesting

ดูตัวอย่างการทดสอบย้อนหลังในโฟลเดอร์ `back_test/` และเรียกใช้

```bash
python src/gpt_trader/cli/main_backtest.py --config back_test/backtest.json
```

ไฟล์ผลลัพธ์จะถูกบันทึกใน `data/back_test/signals/`

## Backend API

มีตัวอย่างเซิร์ฟเวอร์ API ใน `backend/neon-ts` ติดตั้ง dependency และรันด้วยคำสั่ง

```bash
cd backend/neon-ts
npm install
npm run build
npm start
```

## CustomIndicator

ไฟล์ `ea/CustomIndicator.mq5` ใช้คำนวณ RSI‑14, SMA‑20 และ ATR‑14 หากเปิดตัวแปร `DisplaySignals` จะอ่านไฟล์สัญญาณล่าสุดมาแสดงบนกราฟ MT5

## การทดสอบ

ติดตั้งไลบรารีก่อนแล้วจึงรัน

```bash
pytest
```

## การแก้ปัญหา

- `MetaTrader5.initialize()` ล้มเหลว – ตรวจสอบ path และสถาปัตยกรรมของ Python
- โมดูลหาย – รัน `./scripts/install_deps.sh`
- ปัญหาการยืนยันตัวตน OpenAI – ตรวจสอบตัวแปร `OPENAI_API_KEY` หรือไฟล์ `gpt.json`

## เอกสารเพิ่มเติม

- [วิธีใช้งานระบบภาษาไทย](live_trade/docs/usage_th.md)
- [คู่มือใช้งาน Live Trade และ Backtest](docs/usage_overall_th.md)
- [สรุปรายการไฟล์ในโครงการ](docs/files_overview_th.md)
- [ภาพรวม flow การทำงาน](docs/flow_overview_th.md)
- [การติดตั้งบน Linux/Wine และใช้งาน scheduler](docs/usage_linux_th.md)
- [การใช้งาน Backend API](docs/backend_usage_th.md)
- [ตัวอย่างตั้งค่า setting_live_trade](live_trade/docs/config_example_th.md)
- [Grafana/Retool dashboards](docs/dashboard.md)

## License

โปรเจ็กต์นี้ใช้สัญญาอนุญาตแบบ [MIT License](LICENSE)
