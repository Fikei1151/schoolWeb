import psycopg2
from psycopg2 import Error

def test_db_connection():
    try:
        # ข้อมูลการเชื่อมต่อจาก RDS
        connection = psycopg2.connect(
            host="school.c5mgc8y4uhqo.us-east-1.rds.amazonaws.com",
            port="5432",
            database="school",
            user="mukhtari-web-flaks",
            password="Fikree240980352350a"
        )

        # สร้าง cursor เพื่อรันคำสั่ง SQL
        cursor = connection.cursor()

        # ทดสอบด้วยการรันคำสั่งง่าย ๆ
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print("เชื่อมต่อสำเร็จ! เวอร์ชัน PostgreSQL:", db_version)

        # ปิด cursor และการเชื่อมต่อ
        cursor.close()
        connection.close()
        print("ปิดการเชื่อมต่อเรียบร้อย")

    except Error as e:
        print("เกิดข้อผิดพลาดในการเชื่อมต่อ:", e)

if __name__ == "__main__":
    test_db_connection()