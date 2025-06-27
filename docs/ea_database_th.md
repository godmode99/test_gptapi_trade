# การเชื่อมต่อ EA กับฐานข้อมูล

ไฟล์นี้แนะนำการส่งคำสั่งซื้อขายจาก EA (MQL5) ไปยังเซิร์ฟเวอร์ API
ที่ใช้บันทึกข้อมูลลงฐานข้อมูล เมื่อทดสอบในเครื่องมักจะเรียกผ่าน URL
`http://localhost:3000` แต่เมื่อ deploy ไปยัง Vercel แล้วต้องเปลี่ยนค่า URL
ให้เป็นโดเมนที่ Vercel กำหนด

## เปลี่ยน URL เป็นโดเมน Vercel

หลังจาก deploy backend แล้ว ให้นำชื่อโดเมนที่ได้จาก Vercel มาแทนที่
`http://localhost:3000` เช่น `https://my-trade-app.vercel.app` เป็นต้น

ตัวอย่างโค้ด MQL5 ที่เรียก API ด้วย `WebRequest`:

```mql5
WebRequest("POST","https://<your-app>.vercel.app/trade", ...);
```

เพียงแก้ไขโดเมนในตัวอย่างข้างต้น EA ก็จะส่งคำสั่งไปยังเซิร์ฟเวอร์ที่ deploy
อยู่บน Vercel ได้ทันที
