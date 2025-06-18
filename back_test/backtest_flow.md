# Backtest Mode Flow

1. วัตถุประสงค์ของ Backtest Mode
   ทดสอบความแม่นของ signal ที่ GPT คิดจากข้อมูลย้อนหลัง

วัด performance ของ AI strategy กับ historical data จริง

2. Overview Flow (จากแผนภาพ/flowchart)

[Config File]
|
[main_backtest.py (Entry)]
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
