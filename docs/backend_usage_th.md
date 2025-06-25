# คู่มือใช้งาน Backend API

เอกสารนี้อธิบายขั้นตอนการติดตั้งและใช้งานเซิร์ฟเวอร์ API ในโฟลเดอร์ `backend/api` ซึ่งพัฒนาโดยใช้ Node.js และ Express.js โดยข้อมูลทั้งหมดจะถูกบันทึกลงฐานข้อมูล Supabase ตาม schema ใน `backend/supabase/schema.sql`.

## 1. ติดตั้งแพ็กเกจ Node.js

```bash
cd backend/api
npm install
```

คำสั่งนี้จะติดตั้ง `express` และ `@supabase/supabase-js` ตามที่ระบุไว้ใน `package.json`.

## 2. กำหนดตัวแปรสภาพแวดล้อม

เซิร์ฟเวอร์จำเป็นต้องรู้ URL และคีย์ของโปรเจกต์ Supabase ก่อนเริ่มทำงาน กำหนดค่าดังนี้

```bash
export SUPABASE_URL="https://<project-ref>.supabase.co"
export SUPABASE_KEY="<service-role-key>"
# เลือกพอร์ตได้ (ค่าเริ่มต้น 3000)
export PORT=3000
```

## 3. รันเซิร์ฟเวอร์

เมื่อกำหนดตัวแปรครบแล้ว สามารถเริ่มเซิร์ฟเวอร์ได้ด้วย

```bash
npm start
# หรือ
node app.js
```

หากไม่มีการระบุค่า `PORT` เซิร์ฟเวอร์จะเปิดที่พอร์ต `3000` โดยจะแสดงข้อความ `API server listening on port 3000` ในคอนโซล

## 4. การใช้งาน API

เซิร์ฟเวอร์มี endpoint สำหรับบันทึกข้อมูล 4 ชนิด ซึ่งจะเขียนลงตารางที่สอดคล้องกันใน Supabase

- `POST /signal` – เพิ่มข้อมูลสัญญาณเข้า table `signals`
- `POST /order` – เพิ่มคำสั่งที่รอเข้าไม้ใน table `pending_orders`
- `POST /trade` – บันทึกผลการเทรดใน table `trades`
- `POST /event` – บันทึกเหตุการณ์ต่าง ๆ ใน table `trade_events`

ตัวอย่างเรียกใช้งานด้วย `curl`

```bash
curl -X POST http://localhost:3000/signal \
     -H "Content-Type: application/json" \
     -d '{"signal_id":"demo_01","symbol":"XAUUSD","entry":2320.5,"sl":2315,"tp":2335,"type":"buy_limit","confidence":80}'
```

ควรตรวจสอบว่าแต่ละคีย์ตรงกับชนิดข้อมูลใน `backend/supabase/schema.sql` ก่อนส่งเข้าระบบ

## 5. เตรียมฐานข้อมูล

หากยังไม่ได้สร้างตาราง สามารถดูวิธีตั้งค่า Supabase ได้ที่ [docs/supabase_setup.md](supabase_setup.md) จากนั้นจึงกำหนดค่า `SUPABASE_URL` และ `SUPABASE_KEY` ตามโปรเจกต์ของคุณ

