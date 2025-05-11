#!/bin/bash

# สคริปต์สำหรับแก้ไขปัญหา DNS ในการเชื่อมต่อกับ Let's Encrypt API

echo "=== เครื่องมือแก้ไขปัญหา DNS สำหรับ Let's Encrypt ==="
echo

# ตรวจสอบว่ารันด้วย sudo หรือไม่
if [ "$EUID" -ne 0 ]; then
  echo "กรุณารันสคริปต์นี้ด้วย sudo"
  echo "ตัวอย่าง: sudo ./bypass_dns.sh"
  exit 1
fi

echo "1. แสดง DNS servers ปัจจุบัน..."
cat /etc/resolv.conf | grep nameserver

echo
echo "2. กำลังทดสอบการเชื่อมต่อกับ Let's Encrypt API..."
if ping -c 1 acme-v02.api.letsencrypt.org > /dev/null 2>&1; then
  echo "✓ สามารถเชื่อมต่อกับ Let's Encrypt API ได้แล้ว"
  echo "ไม่จำเป็นต้องแก้ไขอะไรเพิ่มเติม"
else
  echo "✗ ไม่สามารถเชื่อมต่อกับ Let's Encrypt API ได้"
  echo
  echo "3. กำลังสำรองไฟล์ /etc/resolv.conf..."
  cp /etc/resolv.conf /etc/resolv.conf.backup
  echo "✓ สำรองไฟล์เรียบร้อยแล้วที่ /etc/resolv.conf.backup"
  
  echo
  echo "4. กำลังเพิ่ม Google DNS..."
  echo "nameserver 8.8.8.8" > /etc/resolv.conf
  echo "nameserver 8.8.4.4" >> /etc/resolv.conf
  echo "✓ เพิ่ม Google DNS เรียบร้อยแล้ว"
  
  echo
  echo "5. กำลังทดสอบการเชื่อมต่ออีกครั้ง..."
  if ping -c 1 acme-v02.api.letsencrypt.org > /dev/null 2>&1; then
    echo "✓ สามารถเชื่อมต่อกับ Let's Encrypt API ได้แล้ว"
    echo "ตอนนี้คุณสามารถรันสคริปต์ init-letsencrypt.sh ได้"
  else
    echo "✗ ยังไม่สามารถเชื่อมต่อกับ Let's Encrypt API ได้"
    echo "อาจมีปัญหาอื่นที่ไม่ใช่ DNS กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ตของคุณ"
    echo "หรือลองเพิ่ม hosts entry โดยใช้คำสั่ง:"
    echo "echo \"149.129.136.58 acme-v02.api.letsencrypt.org\" >> /etc/hosts"
  fi
fi

echo
echo "คำแนะนำเพิ่มเติม:"
echo "- หากต้องการกลับไปใช้ค่า DNS เดิม ให้รันคำสั่ง: sudo cp /etc/resolv.conf.backup /etc/resolv.conf"
echo "- การเปลี่ยนแปลงนี้อาจไม่ถาวรขึ้นอยู่กับการตั้งค่าเครือข่ายของระบบปฏิบัติการ"
echo "- ถ้า Docker ใช้ DNS ที่แตกต่างจากระบบ อาจต้องตั้งค่า DNS ให้กับ Docker โดยเฉพาะ"
echo
echo "เสร็จสิ้น!" 