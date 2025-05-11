# โปรเจกต์เว็บโรงเรียน (School Web)

## การติดตั้งด้วย Docker

โปรเจกต์นี้ถูกพัฒนาเพื่อรันบน Docker โดยมีองค์ประกอบหลักคือ:

1. **PostgreSQL** - ฐานข้อมูล
2. **Flask Web Application** - เว็บแอปพลิเคชัน
3. **Docker Volume** - สำหรับเก็บไฟล์ที่อัปโหลด (แทน S3)

### ขั้นตอนการติดตั้ง

1. ตรวจสอบให้แน่ใจว่าได้ติดตั้ง Docker และ Docker Compose บนเครื่อง

2. คัดลอกไฟล์ `.env.example` เป็น `.env` และแก้ไขค่าตามต้องการ
   ```
   cp .env.example .env
   ```

3. รันคำสั่ง Docker Compose เพื่อสร้างและเริ่มต้นคอนเทนเนอร์
   ```
   docker-compose up -d
   ```

4. เมื่อรันเสร็จแล้ว สามารถเข้าถึงแอปพลิเคชันได้ที่:
   - Web Application: http://localhost:8001

### รายละเอียดพอร์ต

- PostgreSQL: 5433 (ภายนอก) -> 5432 (ภายใน)
- Flask Web: 8001 (ภายนอก) -> 8000 (ภายใน)

### การจัดการข้อมูล

- ข้อมูลของ PostgreSQL จะถูกเก็บใน volume ชื่อ `postgres_data`
- ไฟล์ที่อัปโหลดจะถูกเก็บใน volume ชื่อ `file_storage` 

### คำสั่งพื้นฐาน

```
# เริ่มต้นการทำงาน
docker-compose up -d

# หยุดการทำงาน
docker-compose down

# ดูล็อก
docker-compose logs -f

# เข้าไปใน container (shell)
docker-compose exec web bash
docker-compose exec db bash

# Migration (ถ้าใช้ Flask-Migrate)
docker-compose exec web flask db upgrade
```

### การสำรองข้อมูล

การสำรองฐานข้อมูล:
```
docker-compose exec db pg_dump -U schoolweb schoolwebdb > backup.sql
```

การนำเข้าข้อมูล:
```
cat backup.sql | docker-compose exec -T db psql -U schoolweb schoolwebdb
```

## หมายเหตุการย้ายจาก AWS S3

ระบบนี้ได้รับการปรับให้ใช้ Local Storage แทน AWS S3 เพื่อลดค่าใช้จ่าย โดยฟังก์ชันใน utils/s3_utils.py ยังคงชื่อเดิมแต่ถูกปรับให้ทำงานกับไฟล์ในระบบแทน 

## การตั้งค่าโดเมนและ SSL สำหรับ mukhtati.ac.th

### ขั้นตอนการตั้งค่า Nginx สำหรับโดเมน

1. **เตรียมเซิร์ฟเวอร์** ให้เข้าสู่ระบบเซิร์ฟเวอร์ของคุณด้วย SSH
   ```
   ssh username@your_server_ip
   ```

2. **ติดตั้ง Docker และ Docker Compose** ถ้ายังไม่ได้ติดตั้ง
   ```
   sudo apt update
   sudo apt install docker.io docker-compose -y
   ```

3. **ตั้งค่า DNS ของโดเมน**
   - เข้าไปที่ผู้ให้บริการโดเมนของคุณ (เช่น GoDaddy, Namecheap, หรือ Thai Name Server)
   - สร้าง A record สำหรับ `mukhtati.ac.th` และ `www.mukhtati.ac.th` ที่ชี้ไปที่ IP ของเซิร์ฟเวอร์คุณ
   - รอให้การเปลี่ยนแปลง DNS มีผล (อาจใช้เวลา 24-48 ชั่วโมง)

4. **โคลน Git Repository**
   ```
   git clone https://github.com/your-username/schoolWeb.git
   cd schoolWeb
   ```

5. **ตั้งค่าไฟล์ .env**
   ```
   cp .env.example .env
   # แก้ไขค่าในไฟล์ .env ตามต้องการ
   ```

6. **การตั้งค่าพอร์ตเมื่อเซิร์ฟเวอร์มีการใช้งานพอร์ต 80/443 อยู่แล้ว**
   
   เราได้ปรับพอร์ตของ Nginx ให้ใช้งานพอร์ต 8080/8443 แทนเพื่อหลีกเลี่ยงความขัดแย้ง:
   
   - พอร์ต HTTP: 8080 (แทน 80)
   - พอร์ต HTTPS: 8443 (แทน 443)
   
   คุณมีทางเลือกเพิ่มเติม:
   
   a) **ใช้พอร์ตทางเลือก** (แนะนำสำหรับการทดสอบ):
      - ไม่ต้องแก้ไขอะไรเพิ่มเติม เข้าถึงเว็บไซต์ผ่าน `http://mukhtati.ac.th:8080` หรือ `https://mukhtati.ac.th:8443`
   
   b) **ตั้งค่า Reverse Proxy เพิ่มเติม** (แนะนำสำหรับการใช้งานจริง):
      - ใช้ Nginx หลักที่อยู่บนพอร์ต 80/443 ในการ reverse proxy ไปยังเว็บแอปพลิเคชันของคุณที่รันบนพอร์ต 8080/8443
      
      ตัวอย่างการตั้งค่า Nginx สำหรับ reverse proxy:
      ```
      server {
          listen 80;
          server_name mukhtati.ac.th www.mukhtati.ac.th;
          
          location / {
              proxy_pass http://localhost:8080;
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
          }
      }
      
      server {
          listen 443 ssl;
          server_name mukhtati.ac.th www.mukhtati.ac.th;
          
          # ใส่ SSL configuration ที่นี่
          
          location / {
              proxy_pass https://localhost:8443;
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
          }
      }
      ```

7. **รัน init-letsencrypt.sh เพื่อตั้งค่า SSL certificates**
   ```
   sudo ./init-letsencrypt.sh
   ```

8. **เริ่มระบบด้วย Docker Compose**
   ```
   docker-compose up -d
   ```

### การต่ออายุ SSL certificates

Let's Encrypt certificates มีอายุ 90 วัน สามารถต่ออายุอัตโนมัติด้วยการเพิ่ม cron job:

```
sudo crontab -e
```

เพิ่มบรรทัดนี้เพื่อรันสคริปต์ต่ออายุทุกวันที่ 1 ของเดือน:

```
0 0 1 * * docker-compose -f /path/to/schoolWeb/docker-compose.yml run --rm mukhtari_certbot renew && docker-compose -f /path/to/schoolWeb/docker-compose.yml restart nginx
```

### การแก้ไขปัญหาทั่วไป

1. **ตรวจสอบสถานะของ containers**
   ```
   docker-compose ps
   ```

2. **ดูล็อกของ Nginx**
   ```
   docker-compose logs nginx
   ```

3. **ดูล็อกของ Certbot**
   ```
   docker-compose logs certbot
   ```

4. **รีสตาร์ท Nginx เมื่อมีการเปลี่ยนแปลงไฟล์คอนฟิก**
   ```
   docker-compose restart nginx
   ```