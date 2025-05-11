#!/bin/bash

# สคริปต์สำหรับการเริ่มต้นใช้งาน Let's Encrypt SSL บน Docker และ Nginx

if ! [ -x "$(command -v docker-compose)" ]; then
  echo 'Error: docker-compose is not installed.' >&2
  exit 1
fi

# ตรวจสอบการเชื่อมต่ออินเทอร์เน็ตและ DNS
echo "### ตรวจสอบการเชื่อมต่ออินเทอร์เน็ตและ DNS ..."
if ! ping -c 1 google.com > /dev/null 2>&1; then
  echo "Error: ไม่สามารถเชื่อมต่ออินเทอร์เน็ตได้ กรุณาตรวจสอบการเชื่อมต่อของคุณ"
  exit 1
fi

# ตรวจสอบว่าสามารถเข้าถึง Let's Encrypt API ได้หรือไม่
if ! ping -c 1 acme-v02.api.letsencrypt.org > /dev/null 2>&1; then
  echo "Error: ไม่สามารถเข้าถึง Let's Encrypt API ได้"
  echo "กำลังตรวจสอบปัญหา DNS ..."

  # ตรวจสอบ DNS server
  if [ -f /etc/resolv.conf ]; then
    echo "DNS servers ที่กำลังใช้งาน:"
    grep "nameserver" /etc/resolv.conf
    
    # ลอง nslookup โดยใช้ Google DNS
    echo "กำลังทดลองใช้ Google DNS (8.8.8.8) ..."
    if ! nslookup acme-v02.api.letsencrypt.org 8.8.8.8 > /dev/null 2>&1; then
      echo "ยังไม่สามารถแก้ไขชื่อโดเมนได้แม้แต่ด้วย Google DNS"
    else
      echo "สามารถแก้ไขชื่อโดเมนได้ด้วย Google DNS"
      echo "แนะนำให้แก้ไขไฟล์ /etc/resolv.conf เพื่อใช้ Google DNS (8.8.8.8, 8.8.4.4)"
    fi
  fi
  
  echo "แนะนำให้ตรวจสอบการตั้งค่า DNS บนเซิร์ฟเวอร์ของคุณ"
  echo "เพิ่มบรรทัดต่อไปนี้ในไฟล์ /etc/resolv.conf:"
  echo "nameserver 8.8.8.8"
  echo "nameserver 8.8.4.4"
  
  exit 1
fi

domains=("mukhtari.ac.th" "www.mukhtari.ac.th")
rsa_key_size=4096
data_path="./certbot"
email="fikree205m@gmail.com" # ใส่อีเมลที่จะใช้สำหรับการแจ้งเตือนจาก Let's Encrypt
staging=1 # ตั้งค่าเป็น 1 เพื่อการทดสอบ (จะไม่สร้าง certificate จริง)

if [ -d "$data_path" ]; then
  read -p "โฟลเดอร์ $data_path มีอยู่แล้ว (certificates อาจจะมีอยู่แล้ว). ต้องการลบและเริ่มใหม่หรือไม่? (y/N): " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
  rm -rf "$data_path"
fi

# สร้างโฟลเดอร์ทั้งหมดที่จำเป็น
mkdir -p "$data_path/conf/live/${domains[0]}"
mkdir -p "$data_path/data"
mkdir -p "$data_path/www"

echo "### สร้างแฟ้ม dummy certificate สำหรับ ${domains[0]} ..."
openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1 \
  -keyout "$data_path/conf/live/${domains[0]}/privkey.pem" \
  -out "$data_path/conf/live/${domains[0]}/fullchain.pem" \
  -subj "/CN=localhost" 2>/dev/null

# ตรวจสอบว่า certificates มีอยู่จริง
if [ ! -f "$data_path/conf/live/${domains[0]}/privkey.pem" ] || [ ! -f "$data_path/conf/live/${domains[0]}/fullchain.pem" ]; then
  echo "Error: Failed to create dummy certificates"
  exit 1
fi

echo "### เริ่มต้น nginx ..."
docker-compose down
docker-compose up -d nginx || { echo "เกิดข้อผิดพลาดในการเริ่ม nginx"; exit 1; }

# รอให้ nginx พร้อมใช้งาน
sleep 5

echo "### แก้ไขปัญหา DNS สำหรับ Let's Encrypt API ..."
echo "กำลังเพิ่มการตั้งค่า DNS ชั่วคราวในคอนเทนเนอร์ certbot ..."

echo "### ขอใบรับรอง SSL จริงจาก Let's Encrypt ..."
# เพิ่ม verbose logging เพื่อแสดงข้อผิดพลาดอย่างละเอียด
# ใช้ --dry-run เพื่อทดสอบกระบวนการโดยไม่ทำการสร้าง certificate จริง
if [ $staging != "0" ]; then
  staging_arg="--staging"
else
  staging_arg=""
fi

# ใช้ Docker exec เพื่อกำหนดค่า DNS ภายในคอนเทนเนอร์ certbot ก่อนเรียกใช้งาน
docker-compose run --rm --entrypoint "/bin/sh" certbot -c "echo 'nameserver 8.8.8.8' > /etc/resolv.conf && echo 'nameserver 8.8.4.4' >> /etc/resolv.conf && /usr/bin/certbot certonly --webroot -w /var/www/certbot $staging_arg --dry-run -v --email $email -d ${domains[0]} -d ${domains[1]} --rsa-key-size $rsa_key_size --agree-tos --no-eff-email --force-renewal" || { 
  echo "เกิดข้อผิดพลาดในการขอใบรับรอง SSL"; 
  echo "ลองตรวจสอบข้อมูลโดเมนและการตั้งค่า DNS";
  exit 1; 
}

echo "### ทดสอบการขอ certificate สำเร็จ! กำลังขอใบรับรองที่สามารถใช้งานได้จริง..."
# หลังจากทดสอบสำเร็จ จึงขอใบรับรองจริง (ถ้าไม่ได้อยู่ในโหมด staging)
if [ $staging = "0" ]; then
  docker-compose run --rm --entrypoint "/bin/sh" certbot -c "echo 'nameserver 8.8.8.8' > /etc/resolv.conf && echo 'nameserver 8.8.4.4' >> /etc/resolv.conf && /usr/bin/certbot certonly --webroot -w /var/www/certbot --email $email -d ${domains[0]} -d ${domains[1]} --rsa-key-size $rsa_key_size --agree-tos --no-eff-email --force-renewal" || { 
    echo "เกิดข้อผิดพลาดในการขอใบรับรอง SSL จริง"; 
    exit 1; 
  }
fi

echo "### เสร็จสิ้น! ทำการรีสตาร์ท nginx ..."
docker-compose restart nginx || { echo "เกิดข้อผิดพลาดในการรีสตาร์ท nginx"; exit 1; }

echo "### คำแนะนำเพิ่มเติม:"
echo "1. ในการทดสอบ สคริปต์จะใช้โหมด staging และ dry-run"
echo "2. เพื่อขอใบรับรองจริง ให้แก้ไข staging=0 ในสคริปต์นี้ และรันใหม่อีกครั้ง"
echo "3. ตรวจสอบให้แน่ใจว่า DNS ของโดเมน ${domains[0]} และ ${domains[1]} ชี้มาที่ IP ของเซิร์ฟเวอร์นี้"
echo "4. ตรวจสอบว่าพอร์ต 80 และ 443 เปิดไว้ในไฟร์วอลล์"
echo "5. หากยังมีปัญหาเรื่อง DNS ลองเพิ่ม DNS servers ในไฟล์ /etc/resolv.conf ของเซิร์ฟเวอร์:"
echo "   nameserver 8.8.8.8"
echo "   nameserver 8.8.4.4" 