# การใช้งานบน Linux (Wine)

เอกสารนี้อธิบายขั้นตอนติดตั้ง MetaTrader 5 ผ่าน Wine การเตรียมไลบรารี Python และการใช้งาน scheduler สำหรับรันระบบอัตโนมัติบน Linux

## 1. ติดตั้ง Wine และ MetaTrader 5

1. ติดตั้งแพ็กเกจ Wine ตามวิธีของแต่ละดิสโทร ตัวอย่างบน Ubuntu:
   ```bash
   sudo apt install wine
   ```
2. ดาวน์โหลดตัวติดตั้ง MetaTrader 5 เวอร์ชัน Windows แล้วรันผ่าน Wine
3. หลังติดตั้งจะได้ไฟล์ `terminal64.exe` ภายใต้เส้นทางที่คล้ายกับ
   `~/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe`
4. หาก `mt5.initialize()` ไม่พบโปรแกรม ให้ระบุ path ดังกล่าวในไฟล์คอนฟิกหรือโค้ดที่เรียก

## 2. ติดตั้งไลบรารี Python

ใช้สคริปต์ `scripts/install_deps.sh` เพื่อติดตั้งไลบรารีที่กำหนดไว้ใน `requirements.txt`

```bash
./scripts/install_deps.sh
```

สคริปต์นี้รวมถึงการติดตั้ง `APScheduler` ซึ่งใช้โดย scheduler ของระบบ

## 3. การใช้งาน scheduler

เรียก `src/gpt_trader/cli/scheduler_liveTrade.py` เพื่อตั้งเวลารัน `main_liveTrade.py` ซ้ำ ๆ

ตัวอย่างเริ่มต้นใน 15 นาที แล้วทำงานทุก 60 นาที:

```bash
python src/gpt_trader/cli/scheduler_liveTrade.py --start-in 15 --interval 60
```

กด **Ctrl+C** เพื่อหยุดการทำงานของ scheduler
