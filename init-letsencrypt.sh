#!/bin/bash

# สคริปต์สำหรับการเริ่มต้นใช้งาน Let's Encrypt SSL บน Docker และ Nginx

if ! [ -x "$(command -v docker-compose)" ]; then
  echo 'Error: docker-compose is not installed.' >&2
  exit 1
fi

domains=(mukhtati.ac.th www.mukhtati.ac.th)
rsa_key_size=4096
data_path="./certbot"
email="admin@mukhtati.ac.th" # ใส่อีเมลที่จะใช้สำหรับการแจ้งเตือนจาก Let's Encrypt
staging=0 # ตั้งค่าเป็น 1 ถ้าต้องการทดสอบ (ไม่สร้าง certificate จริง)

if [ -d "$data_path" ]; then
  read -p "โฟลเดอร์ $data_path มีอยู่แล้ว (certificates อาจจะมีอยู่แล้ว). ต้องการลบและเริ่มใหม่หรือไม่? (y/N): " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
  rm -rf "$data_path"
fi

mkdir -p "$data_path/conf/live/$domains"
mkdir -p "$data_path/data"

echo "### สร้างแฟ้ม dummy certificate สำหรับ $domains ..."
openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1 \
  -keyout "$data_path/conf/live/$domains[0]/privkey.pem" \
  -out "$data_path/conf/live/$domains[0]/fullchain.pem" \
  -subj "/CN=localhost"

echo "### เริ่มต้น nginx ..."
docker-compose up -d nginx

echo "### ขอใบรับรอง SSL จริงจาก Let's Encrypt ..."
docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $email \
    -d ${domains[0]} -d ${domains[1]} \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot

echo "### เสร็จสิ้น! ทำการรีสตาร์ท nginx ..."
docker-compose restart nginx 