from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from database import db
from models.user import User, StudentProfile, GuardianProfile
from datetime import datetime

user_bp = Blueprint('user', __name__)

UPLOAD_FOLDER = 'static/profile_pics/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(file, user):
    """ บันทึกภาพโปรไฟล์เป็น `citizen_id.png` และทับภาพเก่า """
    if file and allowed_file(file.filename):
        filename = f"{user.citizen_id}.png"  # ✅ ใช้ citizen_id เป็นชื่อไฟล์
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # ลบไฟล์เก่าก่อน
        if os.path.exists(file_path):
            os.remove(file_path)
        
        file.save(file_path)
        return filename  # ✅ คืนค่าชื่อไฟล์
    return None

@user_bp.route('/profile')
@login_required
def profile():
    """ แสดงโปรไฟล์ของผู้ใช้ """
    if current_user.role == 'student' and current_user.student_profile:
        education_level = current_user.student_profile.education_level or "ไม่ระบุ"
        return render_template('user/student_profile.html', student=current_user.student_profile, education_level=education_level)
    return render_template('user/profile.html', user=current_user)

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
            user.email = data.get('email', user.email)
            user.phone = data.get('phone', user.phone)
            user.address = data.get('address', user.address)

        # ✅ อัปโหลดรูปโปรไฟล์
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            filename = save_profile_image(file, user)
            if filename:
                user.profile_image = f"static/profile_pics/{filename}"
                

        db.session.commit()
        flash('อัปเดตโปรไฟล์สำเร็จ!', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/edit_profile.html', user=current_user)

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

        # ✅ อัปโหลดรูปโปรไฟล์
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            filename = save_profile_image(file, current_user)
            if filename:
                current_user.profile_image = f"static/profile_pics/{filename}"

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

    return render_template('user/edit_student_profile.html', student=student, guardian=guardian)
