# คู่มือใช้งาน Backend API

เอกสารนี้อธิบายการตั้งค่าและใช้งานเซิร์ฟเวอร์ Backend ซึ่งแบ่งโครงสร้างดังนี้

1. **`backend/api`** – เวอร์ชันปัจจุบันเขียนด้วย TypeScript ใช้โมดูล `pg` เชื่อมฐานข้อมูลผ่านตัวแปร `DATABASE_URL`
   โค้ดหลักอยู่ที่ `app.ts` และ `services/db.ts`
2. **`backend/neon-ts`** – เวอร์ชัน TypeScript เชื่อมฐานข้อมูล Neon ด้วยไลบรารี `@neondatabase/serverless` ผ่านตัวแปร `DATABASE_URL`

ผู้ที่ไม่เคยใช้ Node.js มาก่อนก็สามารถทำตามขั้นตอนต่อไปนี้ได้

## 1. เตรียมเครื่องมือพื้นฐาน

1. ติดตั้ง Node.js เวอร์ชัน LTS จาก <https://nodejs.org>
   เมื่อติดตั้งเสร็จให้ตรวจสอบด้วย
   ```bash
   node -v
   npm -v
   ```
   หากแสดงหมายเลขเวอร์ชันแสดงว่าใช้งานได้แล้ว
2. ติดตั้งไลบรารีที่ใช้ในโปรเจกต์
  ```bash
  cd backend/api
  npm install
  npm run build
  ```
  คำสั่งนี้จะดาวน์โหลดแพ็กเกจใน `package.json` เช่น `express` และ `@neondatabase/serverless`

  หากใช้เวอร์ชัน TypeScript ให้ติดตั้งไลบรารีและคอมไพล์ภายใต้ `backend/neon-ts`

  ```bash
  cd backend/neon-ts
  npm install
  npm run build
  ```

## 2. กำหนดตัวแปรสภาพแวดล้อม

เซิร์ฟเวอร์ต้องรู้ข้อมูลเชื่อมต่อกับฐานข้อมูลและพอร์ตที่เปิดบริการ ตัวอย่างการตั้งค่ามีดังนี้

```bash
# ใช้ร่วมกันทั้งสองเวอร์ชัน
export DATABASE_URL="postgres://<user>:<pass>@<host>/<db>"
export PORT=3000  # เปลี่ยนได้ตามต้องการ
```

ค่าตัวแปรดูได้จากหน้า **Settings → API** ในโปรเจกต์ หรือจากแดชบอร์ดของ Neon หากไม่กำหนด `PORT` จะใช้ค่าเริ่มต้น 3000
## 3. รันเซิร์ฟเวอร์

เมื่อกำหนดค่าครบแล้วให้เริ่มเซิร์ฟเวอร์ด้วย

```bash
npm start
```

หากทุกอย่างถูกต้อง คอนโซลจะแสดงข้อความ `API server listening on port 3000`

## 4. Endpoint ที่ให้บริการ

เซิร์ฟเวอร์มี 4 เส้นทางสำหรับรับข้อมูลและบันทึกลงฐานข้อมูล

- `POST /signal` – บันทึกสัญญาณเทรดลงตาราง `signals`
- `POST /order` – บันทึกรายการคำสั่งรอเข้าตลาดใน `pending_orders`
- `POST /trade` – บันทึกผลการเทรดจริงใน `trades`
- `POST /event` – บันทึกเหตุการณ์ต่าง ๆ ใน `trade_events`

ควรส่งข้อมูลเป็น JSON ให้ครบตาม schema ไม่เช่นนั้นจะได้รับข้อความ error กลับมา

ตัวอย่างเรียก `POST /signal` ด้วย `curl`

```bash
curl -X POST http://localhost:3000/signal \
     -H 'Content-Type: application/json' \
     -d '{"signal_id":"demo_01","symbol":"XAUUSD","entry":2320.5,"sl":2315,"tp":2335,"type":"buy_limit","confidence":80}'
```

## 5. การเตรียมฐานข้อมูล
 
ในการใช้งานจริงต้องสร้างตารางในฐานข้อมูลก่อน ตัวอย่าง schema จัดเก็บไว้ที่ `backend/schema.sql` ใช้คำสั่งต่อไปนี้เพื่อสร้างตาราง `signals` ใน PostgreSQL

```bash
psql "$DATABASE_URL" -f backend/schema.sql
```

ไฟล์นี้จะสร้างตาราง `signals` สำหรับเก็บข้อมูลที่ได้จากการ parse คำตอบของ GPT (ไฟล์ JSON ล่าสุด) ซึ่งส่งผ่าน endpoint `/signal` ของ API



## 6. Deploy โปรเจกต์ขึ้น Vercel และ Neon

สำหรับเวอร์ชัน TypeScript สามารถนำไป deploy บน Vercel ได้ง่าย ๆ ขั้นตอนโดยสรุปคือ

1. สร้างบัญชี Vercel และเชื่อมต่อรีโปนี้
2. ตั้งค่า Environment Variable ชื่อ `DATABASE_URL` ให้ชี้ไปยังฐานข้อมูล Neon ของคุณ
3. กด **Deploy** หรือใช้คำสั่ง
   ```bash
   vercel --prod
   ```
เมื่อ deploy เสร็จ API จะพร้อมใช้งานผ่าน URL ของ Vercel
