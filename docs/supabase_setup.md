# การตั้งค่า Supabase

ระบบนี้บันทึกข้อมูลการเทรดไว้ในฐานข้อมูล PostgreSQL บน Supabase ไฟล์สำหรับสร้างตารางอยู่ที่ `backend/supabase/schema.sql`

## 1. เตรียมบัญชีและโปรเจกต์

1. สมัครสมาชิกที่ <https://supabase.com> และเข้าสู่ระบบ
2. กด **New Project** ตั้งชื่อโปรเจกต์และรหัสผ่านฐานข้อมูล รอสักครู่จนระบบสร้างเสร็จ

## 2. ติดตั้งและตั้งค่า Supabase CLI

1. ติดตั้ง Node.js หากยังไม่มี จากนั้นรัน
   ```bash
   npm install -g supabase
   ```
2. เข้าสู่ระบบผ่าน CLI
   ```bash
   supabase login
   ```
   นำ access token จากหน้าเว็บมาวางตามที่ระบบถาม

## 3. นำ schema เข้าสู่ฐานข้อมูล

1. คัดลอกค่า **Connection string** จากหน้า **Settings → Database** ของโปรเจกต์ เช่น
   `postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres`
2. ตั้งค่าการเชื่อมต่อให้ CLI
   ```bash
   supabase db remote set 'postgresql://...'
   ```
3. จาก root ของโปรเจกต์ รันคำสั่ง
   ```bash
   supabase db push backend/supabase/schema.sql
   ```
   CLI จะสร้างตารางตามไฟล์ `schema.sql` ให้อัตโนมัติ หากไม่ใช้ CLI สามารถเปิด SQL editor บนเว็บแล้ววางไฟล์ไปรันได้เช่นกัน

## 4. กำหนดตัวแปรสภาพแวดล้อม

หลังจากสร้างตารางแล้ว ให้กำหนดตัวแปรดังนี้เพื่อให้โค้ดเชื่อมต่อได้

```bash
export SUPABASE_URL='https://<project-ref>.supabase.co'
export SUPABASE_KEY='<service-role-key>'
```

ดูค่าทั้งสองได้จากหน้า **Settings → API** ในโปรเจกต์ของคุณ
