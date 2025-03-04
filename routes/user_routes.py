from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from markupsafe import Markup
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from database import db
from models.user import User, StudentProfile, GuardianProfile
from datetime import datetime
from config import Config
from utils.s3_utils import upload_file_to_s3  # นำเข้าฟังก์ชันอัปโหลดไป S3

user_bp = Blueprint('user', __name__)

# ใช้ค่าจาก Config
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS

# สร้างโฟลเดอร์ local สำหรับ fallback ถ้า S3 ไม่ทำงาน
UPLOAD_FOLDER = 'static/profile_pics/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_profile_image_url(image_path):
    """แปลง path หรือ URL ของรูปโปรไฟล์ให้ถูกต้อง"""
    if not image_path:
        return url_for('static', filename='profile_pics/default_profile.png')
    
    # ถ้าเป็น URL เต็ม (S3) ให้ใช้โดยตรง
    if image_path.startswith('http'):
        return image_path
    
    # ถ้าเป็น local path ให้แปลงเป็น URL
    return url_for('static', filename=image_path.replace('static/', ''))

def save_profile_image(file, user):
    """ บันทึกภาพโปรไฟล์เป็น `citizen_id.png` และอัปโหลดไป S3 """
    if file and allowed_file(file.filename):
        filename = f"{user.citizen_id}.png"  # ✅ ใช้ citizen_id เป็นชื่อไฟล์
        
        # ตรวจสอบว่าไฟล์มีข้อมูลจริงหรือไม่
        try:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # กลับไปที่ต้นไฟล์
            
            if file_size == 0:
                flash('ไฟล์ว่างเปล่า กรุณาอัปโหลดไฟล์ใหม่', 'danger')
                return None
            
            # อ่านข้อมูลไฟล์ทั้งหมด
            file_data = file.read()
            file.seek(0)  # กลับไปที่ต้นไฟล์
            
            # สร้าง FileStorage ใหม่จากข้อมูลที่อ่านมา
            from io import BytesIO
            from werkzeug.datastructures import FileStorage
            
            new_file = FileStorage(
                stream=BytesIO(file_data),
                filename=file.filename,
                content_type=file.content_type
            )
            
            # อัปโหลดไป S3
            s3_url = upload_file_to_s3(new_file, "profile_pics", filename)
            if s3_url:
                return s3_url  # คืนค่า URL เต็มจาก S3
            
            # Fallback: บันทึกลงเครื่องถ้า S3 ไม่ทำงาน
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # ลบไฟล์เก่าก่อน
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # บันทึกไฟล์ลงเครื่อง
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            return f"static/profile_pics/{filename}"  # คืนค่า path ในเครื่อง
            
        except ValueError as e:
            flash('เกิดข้อผิดพลาดในการอัปโหลดไฟล์ กรุณาลองใหม่อีกครั้ง', 'danger')
            print(f"File error: {e}")
        except Exception as e:
            flash('เกิดข้อผิดพลาดที่ไม่คาดคิด กรุณาลองใหม่อีกครั้ง', 'danger')
            print(f"Unexpected error: {e}")
    
    return None

@user_bp.route('/profile')
@login_required
def profile():
    """ แสดงโปรไฟล์ของผู้ใช้ """
    # แปลง URL รูปโปรไฟล์ให้ถูกต้อง
    profile_image_url = get_profile_image_url(current_user.profile_image)
    
    if current_user.role == 'student' and current_user.student_profile:
        education_level = current_user.student_profile.education_level or "ไม่ระบุ"
        return render_template('user/student_profile.html', 
                              student=current_user.student_profile, 
                              education_level=education_level,
                              profile_image_url=profile_image_url)
    
    return render_template('user/profile.html', 
                          user=current_user,
                          profile_image_url=profile_image_url)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """ แก้ไขโปรไฟล์ของผู้ใช้ """
    if request.method == 'POST':
        data = request.form
        user = User.query.get(current_user.id)

        if current_user.role == 'student' and user.student_profile:
            student = user.student_profile
            student.full_name_th = data.get('full_name_th', student.full_name_th)
            student.full_name_en = data.get('full_name_en', student.full_name_en)
            student.birth_date = datetime.strptime(data.get('birth_date'), "%Y-%m-%d") if data.get('birth_date') else student.birth_date
            student.nationality = data.get('nationality', student.nationality)
        else:
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            
            # ถ้าอีเมลเป็นค่าว่าง ให้บันทึกเป็น NULL แทน
            email = data.get('email', user.email)
            user.email = None if email == '' else email
            
            # ถ้าเบอร์โทรเป็นค่าว่าง ให้บันทึกเป็น NULL แทน
            phone = data.get('phone', user.phone)
            user.phone = None if phone == '' else phone
            
            # ถ้าที่อยู่เป็นค่าว่าง ให้บันทึกเป็น NULL แทน
            address = data.get('address', user.address)
            user.address = None if address == '' else address

        # ✅ อัปโหลดรูปโปรไฟล์ไป S3
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            file_url = save_profile_image(file, user)
            if file_url:
                # ตรวจสอบว่าเป็น URL หรือ local path
                if file_url.startswith('http'):
                    user.profile_image = file_url  # บันทึก URL เต็ม
                else:
                    user.profile_image = file_url  # บันทึก local path

        db.session.commit()
        flash('อัปเดตโปรไฟล์สำเร็จ!', 'success')
        return redirect(url_for('user.profile'))

    # แปลง URL รูปโปรไฟล์ให้ถูกต้อง
    profile_image_url = get_profile_image_url(current_user.profile_image)
    
    return render_template('user/edit_profile.html', 
                          user=current_user,
                          profile_image_url=profile_image_url)

@user_bp.route('/profile/edit_student', methods=['GET', 'POST'])
@login_required
def edit_student_profile():
    """หน้าแก้ไขข้อมูลนักเรียนและผู้ปกครอง"""
    student = current_user.student_profile
    if not student:
        flash("ไม่มีข้อมูลนักเรียนสำหรับบัญชีนี้", "danger")
        return redirect(url_for('user.profile'))

    guardian = student.guardian  # ดึงข้อมูลผู้ปกครองถ้ามี

    if request.method == 'POST':
        data = request.form

        student.full_name_th = data.get('full_name_th', student.full_name_th)
        student.full_name_en = data.get('full_name_en', student.full_name_en)
        student.birth_date = datetime.strptime(data.get('birth_date'), "%Y-%m-%d") if data.get('birth_date') else student.birth_date
        student.nationality = data.get('nationality', student.nationality)
        current_user.address = data.get('address', current_user.address)
        student.parent_status = data.get('parent_status', student.parent_status)
        student.disability = data.get('disability', student.disability)
        student.special_talent = data.get('special_talent', student.special_talent)

        # ✅ อัปโหลดรูปโปรไฟล์ไป S3
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            file_url = save_profile_image(file, current_user)
            if file_url:
                # ตรวจสอบว่าเป็น URL หรือ local path
                if file_url.startswith('http'):
                    current_user.profile_image = file_url  # บันทึก URL เต็ม
                else:
                    current_user.profile_image = file_url  # บันทึก local path

        # ✅ อัปเดตข้อมูลผู้ปกครอง
        if not guardian:
            guardian = GuardianProfile(student=student)
            db.session.add(guardian)

        guardian.full_name = data.get('guardian_full_name', guardian.full_name)
        guardian.nationality = data.get('guardian_nationality', guardian.nationality)
        guardian.status = data.get('guardian_status', guardian.status)
        guardian.occupation = data.get('guardian_occupation', guardian.occupation)
        guardian.position = data.get('guardian_position', guardian.position)
        guardian.workplace = data.get('guardian_workplace', guardian.workplace)
        guardian.income = data.get('guardian_income', guardian.income)
        guardian.address_no = data.get('guardian_address_no', guardian.address_no)
        guardian.moo = data.get('guardian_moo', guardian.moo)
        guardian.soi = data.get('guardian_soi', guardian.soi)
        guardian.road = data.get('guardian_road', guardian.road)
        guardian.sub_district = data.get('guardian_sub_district', guardian.sub_district)
        guardian.district = data.get('guardian_district', guardian.district)
        guardian.province = data.get('guardian_province', guardian.province)
        guardian.postal_code = data.get('guardian_postal_code', guardian.postal_code)
        guardian.phone = data.get('guardian_phone', guardian.phone)
        guardian.email = data.get('guardian_email', guardian.email)

        db.session.commit()
        flash("อัปเดตข้อมูลนักเรียนและผู้ปกครองเรียบร้อย", "success")
        return redirect(url_for('user.profile'))

    # แปลง URL รูปโปรไฟล์ให้ถูกต้อง
    profile_image_url = get_profile_image_url(current_user.profile_image)
    
    return render_template('user/edit_student_profile.html', 
                          student=student, 
                          guardian=guardian,
                          profile_image_url=profile_image_url)
