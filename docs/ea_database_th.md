# คู่มือการส่งข้อมูลจาก EA เข้า Database

เอกสารนี้อธิบายวิธีปรับแต่ง EA ในโฟลเดอร์ `live_trade/ea` เพื่อส่งข้อมูลคำสั่งซื้อขายไปยังฐานข้อมูลผ่าน Backend API ของโปรเจกต์

## 1. เตรียม Backend API

1. ติดตั้งและรันเซิร์ฟเวอร์ตามขั้นตอนใน [docs/backend_usage_th.md](backend_usage_th.md)
2. ตั้งค่าตัวแปร `DATABASE_URL` และ `PORT` แล้วรันคำสั่ง `npm start`
3. เมื่อเซิร์ฟเวอร์ทำงานแล้วจะรับคำสั่งที่เส้นทาง `POST /trade` เพื่อบันทึกผลการเทรด

## 2. เปิดใช้งาน WebRequest ใน MT5

1. ที่ MetaTrader 5 ไปที่ **Tools → Options → Expert Advisors**
2. เพิ่ม URL ของเซิร์ฟเวอร์ (เช่น `http://localhost:3000`) ในช่อง *Allow WebRequest for listed URL*
3. คลิก **OK** เพื่อบันทึกค่า

## 3. ตัวอย่างโค้ดใน EA

เพิ่มฟังก์ชันส่งข้อมูลหลังจากเปิดออเดอร์ภายใน `LiveTradeEA.mq5` เช่นในเหตุการณ์ `OnTradeTransaction`:

```mql5
void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &req,const MqlTradeResult &res)
  {
   if(trans.type==TRADE_TRANSACTION_ORDER_ADD && res.retcode==10009)
     {
      string json=StringFormat("{\"symbol\":\"%s\",\"volume\":%f,\"price\":%f}",
                               trans.symbol,trans.volume,trans.price);
      char result[];
      string headers="Content-Type: application/json\r\n";
      WebRequest("POST","http://localhost:3000/trade",headers,1000,
                 StringToCharArray(json,result),result);
     }
  }
```

อย่าลืมปรับ URL ให้ตรงกับเซิร์ฟเวอร์ของคุณ และสามารถเพิ่มข้อมูลอื่น ๆ ตาม schema ของตาราง `trades`

## 4. ตรวจสอบผลลัพธ์

เมื่อ EA ส่งคำขอสำเร็จ เซิร์ฟเวอร์จะบันทึกข้อมูลลงตาราง `trades` ในฐานข้อมูล Neon/PostgreSQL
จากนั้นสามารถดูผลผ่านเครื่องมือเช่น `psql`, Grafana หรือ Retool ตามที่อธิบายไว้ในเอกสารอื่น

