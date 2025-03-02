from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort, jsonify, session
from flask_login import login_required, current_user
from database import db
from models.registration import AdmissionPeriod, ExamRoom, StudentApplication
from models.academic import AcademicSettings
from models.user import User, StudentProfile, GuardianProfile
from models.classroom import ClassroomStudents
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid
from functools import wraps
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from flask import make_response

# สร้าง Blueprint
registration_bp = Blueprint('registration', __name__)

# ฟังก์ชันตรวจสอบสิทธิ์ admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# ฟังก์ชันตรวจสอบว่ามีช่วงรับสมัครที่เปิดอยู่หรือไม่
def get_open_admission_periods():
    today = datetime.utcnow().date()
    return AdmissionPeriod.query.filter(
        AdmissionPeriod.is_active == True,
        AdmissionPeriod.start_date <= today,
        AdmissionPeriod.end_date >= today
    ).all()

# ฟังก์ชันสร้าง PDF ใบสมัคร
def generate_application_receipt(application):
    buffer = io.BytesIO()
    
    # สร้าง PDF
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # ลงทะเบียนฟอนต์ภาษาไทย (ต้องมีไฟล์ฟอนต์ในโปรเจค)
    font_path = os.path.join(current_app.root_path, 'temp_download', 'THSarabunNew', 'THSarabunNew.ttf')
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"ไม่พบไฟล์ฟอนต์: {font_path}")
    pdfmetrics.registerFont(TTFont('THSarabun', font_path))
    
    # ตั้งค่าฟอนต์
    p.setFont('THSarabun', 16)
    
    # หัวกระดาษ
    p.setFont('THSarabun', 22)
    p.drawCentredString(width/2, height - 2*cm, "ใบรับสมัครนักเรียน")
    p.setFont('THSarabun', 18)
    p.drawCentredString(width/2, height - 3*cm, f"ปีการศึกษา {application.admission_period.academic_year}")
    p.drawCentredString(width/2, height - 3.7*cm, f"{application.admission_period.education_level} ชั้นปีที่ {application.admission_period.grade_level}")
    
    # เลขที่ใบสมัคร
    p.setFont('THSarabun', 16)
    p.drawString(2*cm, height - 5*cm, f"เลขที่ใบสมัคร: {application.application_number}")
    p.drawString(2*cm, height - 5.7*cm, f"วันที่สมัคร: {application.application_date.strftime('%d/%m/%Y')}")
    
    # ข้อมูลนักเรียน
    p.setFont('THSarabun', 18)
    p.drawString(2*cm, height - 7*cm, "ข้อมูลนักเรียน")
    p.setFont('THSarabun', 16)
    p.drawString(2*cm, height - 8*cm, f"ชื่อ-นามสกุล: {application.first_name} {application.last_name}")
    p.drawString(2*cm, height - 8.7*cm, f"เลขประจำตัวประชาชน: {application.citizen_id}")
    p.drawString(2*cm, height - 9.4*cm, f"เพศ: {application.gender}")
    p.drawString(2*cm, height - 10.1*cm, f"วันเกิด: {application.birth_date.strftime('%d/%m/%Y')}")
    p.drawString(2*cm, height - 10.8*cm, f"สัญชาติ: {application.nationality}")
    
    # ข้อมูลผู้ปกครอง
    p.setFont('THSarabun', 18)
    p.drawString(2*cm, height - 12*cm, "ข้อมูลผู้ปกครอง")
    p.setFont('THSarabun', 16)
    p.drawString(2*cm, height - 13*cm, f"ชื่อ-นามสกุล: {application.guardian_full_name}")
    p.drawString(2*cm, height - 13.7*cm, f"ความสัมพันธ์: {application.guardian_status}")
    p.drawString(2*cm, height - 14.4*cm, f"เบอร์โทรศัพท์: {application.guardian_phone}")
    
    # ข้อมูลห้องสอบ
    if application.exam_room:
        p.setFont('THSarabun', 18)
        p.drawString(2*cm, height - 16*cm, "ข้อมูลห้องสอบ")
        p.setFont('THSarabun', 16)
        p.drawString(2*cm, height - 17*cm, f"ห้องสอบ: {application.exam_room.name}")
        p.drawString(2*cm, height - 17.7*cm, f"สถานที่: {application.exam_room.location}")
        p.drawString(2*cm, height - 18.4*cm, f"วันที่สอบ: {application.exam_room.exam_date.strftime('%d/%m/%Y')}")
        p.drawString(2*cm, height - 19.1*cm, f"เวลาสอบ: {application.exam_room.exam_time}")
    
    # ข้อความท้ายกระดาษ
    p.setFont('THSarabun', 14)
    p.drawCentredString(width/2, 3*cm, "กรุณานำใบรับสมัครนี้มาแสดงในวันสอบ")
    p.drawCentredString(width/2, 2.5*cm, "เอกสารนี้ออกโดยระบบคอมพิวเตอร์")
    
    p.save()
    buffer.seek(0)
    return buffer

# ---- Routes สำหรับผู้ปกครอง (Public) ----

@registration_bp.route('/register')
def register_form():
    """หน้าฟอร์มสมัครเรียน"""
    # ตรวจสอบว่ามีช่วงรับสมัครที่เปิดอยู่หรือไม่
    open_periods = get_open_admission_periods()
    
    if not open_periods:
        return render_template('registration/closed.html')
    
    return render_template('registration/register_form.html', admission_periods=open_periods)

@registration_bp.route('/register', methods=['POST'])
def submit_registration():
    """รับข้อมูลการสมัครจากฟอร์ม"""
    try:
        # ตรวจสอบว่ามีช่วงรับสมัครที่เปิดอยู่หรือไม่
        admission_period_id = request.form.get('admission_period_id')
        if not admission_period_id:
            flash('กรุณาเลือกช่วงเวลารับสมัคร', 'danger')
            return redirect(url_for('registration.register_form'))

        admission_period = AdmissionPeriod.query.get_or_404(admission_period_id)
        
        if not admission_period.is_open():
            flash('ขณะนี้ไม่อยู่ในช่วงเวลารับสมัคร', 'danger')
            return redirect(url_for('registration.register_form'))
        
        # ตรวจสอบว่ามีการสมัครด้วยเลขประจำตัวประชาชนนี้แล้วหรือไม่
        citizen_id = request.form.get('child_citizen_id')
        existing_application = StudentApplication.query.filter_by(citizen_id=citizen_id).first()
        if existing_application:
            flash('มีการสมัครด้วยเลขประจำตัวประชาชนนี้แล้ว กรุณาใช้ฟังก์ชันค้นหาใบสมัคร', 'warning')
            return redirect(url_for('registration.search_form'))
        
        # สร้างเลขที่ใบสมัครก่อน
        application_number = f"APP-{admission_period.academic_year % 100}-{admission_period.education_level[0]}{admission_period.grade_level}-{uuid.uuid4().hex[:4]}"
        
        # สร้างข้อมูลการสมัคร
        new_application = StudentApplication(
            admission_period_id=admission_period_id,
            application_date=datetime.utcnow(),  # ตั้งค่าวันที่สมัคร
            application_number=application_number,  # กำหนดเลขที่ใบสมัคร
            # ข้อมูลนักเรียน
            first_name=request.form.get('child_first_name'),
            last_name=request.form.get('child_last_name'),
            citizen_id=request.form.get('child_citizen_id'),
            gender=request.form.get('child_gender'),
            birth_date=datetime.strptime(request.form.get('child_birth_date'), '%Y-%m-%d').date(),
            nationality=request.form.get('child_nationality'),
            blood_type=request.form.get('child_blood_type'),
            birth_province=request.form.get('child_birth_province'),
            birth_other=request.form.get('child_birth_other'),
            disability=request.form.get('child_disability'),
            special_talent=request.form.get('child_special_talent'),
            # ข้อมูลผู้ปกครอง
            guardian_full_name=request.form.get('guardian_full_name'),
            guardian_nationality=request.form.get('guardian_nationality'),
            guardian_status=request.form.get('guardian_status'),
            guardian_occupation=request.form.get('guardian_occupation'),
            guardian_position=request.form.get('guardian_position'),
            guardian_workplace=request.form.get('guardian_workplace'),
            guardian_income=request.form.get('guardian_income'),
            guardian_address_no=request.form.get('guardian_address_no'),
            guardian_moo=request.form.get('guardian_moo'),
            guardian_soi=request.form.get('guardian_soi'),
            guardian_road=request.form.get('guardian_road'),
            guardian_sub_district=request.form.get('guardian_sub_district'),
            guardian_district=request.form.get('guardian_district'),
            guardian_province=request.form.get('guardian_province'),
            guardian_postal_code=request.form.get('guardian_postal_code'),
            guardian_phone=request.form.get('guardian_phone'),
            guardian_email=request.form.get('guardian_email')
        )
        
        # หาห้องสอบที่เหมาะสม (ยังไม่เต็ม และตรงกับระดับการศึกษา/ชั้นเรียน)
        available_exam_room = ExamRoom.query.filter_by(
            education_level=admission_period.education_level,
            grade_level=admission_period.grade_level,
            academic_year=admission_period.academic_year
        ).first()

        if available_exam_room:
            applications_in_room = StudentApplication.query.filter_by(exam_room_id=available_exam_room.id).count()
            if applications_in_room < available_exam_room.capacity:
                new_application.exam_room_id = available_exam_room.id
            else:
                flash('ห้องสอบเต็มแล้ว กรุณาติดต่อเจ้าหน้าที่', 'warning')
        
        # บันทึกข้อมูล
        db.session.add(new_application)
        db.session.commit()
        
        # Debug: พิมพ์ข้อมูลที่บันทึก
        print(f"บันทึกใบสมัครสำเร็จ: {new_application.id}, {new_application.application_number}")
        
        # เก็บ ID ของใบสมัครใน session เพื่อใช้ในการดาวน์โหลด PDF
        session['application_id'] = new_application.id
        
        flash('ลงทะเบียนสำเร็จ', 'success')
        return redirect(url_for('registration.registration_success'))
        
    except ValueError as ve:
        db.session.rollback()
        print(f"เกิดข้อผิดพลาด ValueError: {str(ve)}")
        flash(f'เกิดข้อผิดพลาดในข้อมูล: {str(ve)} (อาจเกิดจากรูปแบบวันที่ไม่ถูกต้อง)', 'danger')
        return redirect(url_for('registration.register_form'))
    except Exception as e:
        db.session.rollback()
        print(f"เกิดข้อผิดพลาด Exception: {str(e)}")
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        return redirect(url_for('registration.register_form'))

@registration_bp.route('/search')
def search_form():
    """หน้าค้นหาใบสมัคร"""
    return render_template('registration/search.html')

@registration_bp.route('/search', methods=['POST'])
def search_application():
    """ค้นหาใบสมัครด้วยเลขประจำตัวประชาชน"""
    citizen_id = request.form.get('citizen_id')
    
    if not citizen_id:
        flash('กรุณากรอกเลขประจำตัวประชาชน', 'danger')
        return redirect(url_for('registration.search_form'))
    
    application = StudentApplication.query.filter_by(citizen_id=citizen_id).first()
    
    if not application:
        flash('ไม่พบข้อมูลใบสมัครที่ตรงกับเลขประจำตัวประชาชนนี้', 'danger')
        return redirect(url_for('registration.search_form'))
    
    return render_template('registration/search.html', application=application)

@registration_bp.route('/registration-success')
def registration_success():
    """หน้าแสดงผลการสมัครสำเร็จ"""
    application_id = session.get('application_id')
    print(f"application_id ใน session: {application_id}")
    
    if not application_id:
        flash('ไม่พบข้อมูลการสมัคร กรุณาสมัครใหม่หรือค้นหาใบสมัคร', 'danger')
        return redirect(url_for('registration.search_form'))
    
    try:
        application = StudentApplication.query.get(application_id)
        if not application:
            print(f"ไม่พบข้อมูลใบสมัครที่มี ID: {application_id}")
            flash('ไม่พบข้อมูลใบสมัคร กรุณาสมัครใหม่หรือค้นหาใบสมัคร', 'danger')
            return redirect(url_for('registration.search_form'))
        
        print(f"พบข้อมูลใบสมัคร: {application.id}, {application.application_number}")
        return render_template('registration/success.html', application=application)
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในหน้า success: {str(e)}")
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        return redirect(url_for('registration.search_form'))

@registration_bp.route('/download-receipt/<int:application_id>')
def download_receipt(application_id):
    """ดาวน์โหลดใบรับสมัคร PDF"""
    application = StudentApplication.query.get_or_404(application_id)
    
    # สร้าง PDF
    pdf_buffer = generate_application_receipt(application)
    
    # สร้าง response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    
    # Use a simple ASCII filename without any Thai characters
    safe_filename = f'application_{application.id}.pdf'
    
    # Set Content-Disposition header with only ASCII characters
    response.headers['Content-Disposition'] = f'inline; filename={safe_filename}'
    
    return response

# ---- Routes สำหรับ Admin ----

@registration_bp.route('/admin/admission-periods')
@login_required
@admin_required
def admin_admission_periods():
    """หน้าจัดการช่วงเวลารับสมัคร"""
    admission_periods = AdmissionPeriod.query.order_by(
        AdmissionPeriod.academic_year.desc(),
        AdmissionPeriod.education_level,
        AdmissionPeriod.grade_level
    ).all()
    
    # ดึงข้อมูลปีการศึกษาปัจจุบัน
    academic_settings = AcademicSettings.query.first()
    current_year = academic_settings.current_year if academic_settings else datetime.now().year + 543
    
    return render_template(
        'registration/admin/admission_periods.html',
        admission_periods=admission_periods,
        current_year=current_year
    )

@registration_bp.route('/admin/admission-periods/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_admission_period():
    """หน้าสร้างช่วงเวลารับสมัครใหม่"""
    if request.method == 'POST':
        try:
            new_period = AdmissionPeriod(
                academic_year=request.form.get('academic_year'),
                education_level=request.form.get('education_level'),
                grade_level=request.form.get('grade_level'),
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d'),
                end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d'),
                is_active=request.form.get('is_active') == 'on'
            )
            
            db.session.add(new_period)
            db.session.commit()
            
            flash('สร้างช่วงเวลารับสมัครสำเร็จ', 'success')
            return redirect(url_for('registration.admin_admission_periods'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
    
    # ดึงข้อมูลปีการศึกษาปัจจุบัน
    academic_settings = AcademicSettings.query.first()
    current_year = academic_settings.current_year if academic_settings else datetime.now().year + 543
    
    return render_template(
        'registration/admin/create_admission_period.html',
        current_year=current_year
    )

@registration_bp.route('/admin/admission-periods/edit/<int:period_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_admission_period(period_id):
    """หน้าแก้ไขช่วงเวลารับสมัคร"""
    period = AdmissionPeriod.query.get_or_404(period_id)
    
    if request.method == 'POST':
        try:
            period.academic_year = request.form.get('academic_year')
            period.education_level = request.form.get('education_level')
            period.grade_level = request.form.get('grade_level')
            period.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            period.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            period.is_active = request.form.get('is_active') == 'on'
            
            db.session.commit()
            
            flash('แก้ไขช่วงเวลารับสมัครสำเร็จ', 'success')
            return redirect(url_for('registration.admin_admission_periods'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
    
    return render_template(
        'registration/admin/edit_admission_period.html',
        period=period
    )

@registration_bp.route('/admin/exam-rooms')
@login_required
@admin_required
def admin_exam_rooms():
    """หน้าจัดการห้องสอบ"""
    exam_rooms = ExamRoom.query.order_by(
        ExamRoom.academic_year.desc(),
        ExamRoom.education_level,
        ExamRoom.grade_level,
        ExamRoom.name
    ).all()
    
    # ดึงข้อมูลปีการศึกษาปัจจุบัน
    academic_settings = AcademicSettings.query.first()
    current_year = academic_settings.current_year if academic_settings else datetime.now().year + 543
    
    return render_template(
        'registration/admin/exam_rooms.html',
        exam_rooms=exam_rooms,
        current_year=current_year
    )

@registration_bp.route('/admin/exam-rooms/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_exam_room():
    """หน้าสร้างห้องสอบใหม่"""
    if request.method == 'POST':
        try:
            new_room = ExamRoom(
                name=request.form.get('name'),
                capacity=request.form.get('capacity'),
                exam_date=datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d'),
                exam_time=request.form.get('exam_time'),
                location=request.form.get('location'),
                education_level=request.form.get('education_level'),
                grade_level=request.form.get('grade_level'),
                academic_year=request.form.get('academic_year')
            )
            
            db.session.add(new_room)
            db.session.commit()
            
            flash('สร้างห้องสอบสำเร็จ', 'success')
            return redirect(url_for('registration.admin_exam_rooms'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
    
    # ดึงข้อมูลปีการศึกษาปัจจุบัน
    academic_settings = AcademicSettings.query.first()
    current_year = academic_settings.current_year if academic_settings else datetime.now().year + 543
    
    return render_template(
        'registration/admin/create_exam_room.html',
        current_year=current_year
    )

@registration_bp.route('/admin/exam-rooms/edit/<int:room_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_exam_room(room_id):
    """หน้าแก้ไขห้องสอบ"""
    room = ExamRoom.query.get_or_404(room_id)
    
    if request.method == 'POST':
        try:
            room.name = request.form.get('name')
            room.capacity = request.form.get('capacity')
            room.exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d')
            room.exam_time = request.form.get('exam_time')
            room.location = request.form.get('location')
            room.education_level = request.form.get('education_level')
            room.grade_level = request.form.get('grade_level')
            room.academic_year = request.form.get('academic_year')
            
            db.session.commit()
            
            flash('แก้ไขห้องสอบสำเร็จ', 'success')
            return redirect(url_for('registration.admin_exam_rooms'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
    
    return render_template(
        'registration/admin/edit_exam_room.html',
        room=room
    )

@registration_bp.route('/admin/applications')
@login_required
@admin_required
def admin_applications():
    """หน้าจัดการใบสมัคร"""
    # ดึงข้อมูลปีการศึกษาปัจจุบัน
    academic_settings = AcademicSettings.query.first()
    current_year = academic_settings.current_year if academic_settings else datetime.now().year + 543
    
    # ค้นหาตามเงื่อนไข
    academic_year = request.args.get('academic_year', current_year)
    education_level = request.args.get('education_level', '')
    grade_level = request.args.get('grade_level', '')
    status = request.args.get('status', '')
    
    # สร้าง query
    query = StudentApplication.query.join(AdmissionPeriod)
    
    if academic_year:
        query = query.filter(AdmissionPeriod.academic_year == academic_year)
    if education_level:
        query = query.filter(AdmissionPeriod.education_level == education_level)
    if grade_level:
        query = query.filter(AdmissionPeriod.grade_level == grade_level)
    if status:
        query = query.filter(StudentApplication.status == status)
    
    applications = query.order_by(StudentApplication.application_date.desc()).all()
    
    return render_template(
        'registration/admin/applications.html',
        applications=applications,
        current_year=current_year,
        filters={
            'academic_year': academic_year,
            'education_level': education_level,
            'grade_level': grade_level,
            'status': status
        }
    )

@registration_bp.route('/admin/applications/<int:application_id>')
@login_required
@admin_required
def application_detail(application_id):
    """หน้าแสดงรายละเอียดใบสมัคร"""
    application = StudentApplication.query.get_or_404(application_id)
    return render_template(
        'registration/admin/application_detail.html',
        application=application
    )

@registration_bp.route('/admin/applications/update-status/<int:application_id>', methods=['POST'])
@login_required
@admin_required
def update_application_status(application_id):
    """อัปเดตสถานะใบสมัคร"""
    application = StudentApplication.query.get_or_404(application_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'approved', 'rejected']:
        application.status = new_status
        db.session.commit()
        flash('อัปเดตสถานะสำเร็จ', 'success')
    else:
        flash('สถานะไม่ถูกต้อง', 'danger')
    
    return redirect(url_for('registration.application_detail', application_id=application_id))

@registration_bp.route('/admin/applications/assign-exam-room/<int:application_id>', methods=['POST'])
@login_required
@admin_required
def assign_exam_room(application_id):
    """กำหนดห้องสอบให้ผู้สมัคร"""
    application = StudentApplication.query.get_or_404(application_id)
    exam_room_id = request.form.get('exam_room_id')
    
    if exam_room_id:
        exam_room = ExamRoom.query.get_or_404(exam_room_id)
        
        # ตรวจสอบว่าห้องสอบเต็มหรือไม่
        if exam_room.is_full():
            flash('ห้องสอบเต็มแล้ว', 'danger')
        else:
            application.exam_room_id = exam_room_id
            db.session.commit()
            flash('กำหนดห้องสอบสำเร็จ', 'success')
    else:
        flash('กรุณาเลือกห้องสอบ', 'danger')
    
    return redirect(url_for('registration.application_detail', application_id=application_id))

@registration_bp.route('/admin/applications/create-student-account/<int:application_id>', methods=['POST'])
@login_required
@admin_required
def create_student_account(application_id):
    """สร้างบัญชีนักเรียนจากใบสมัคร"""
    application = StudentApplication.query.get_or_404(application_id)
    
    # ตรวจสอบว่าสถานะเป็น approved หรือไม่
    if application.status != 'approved':
        flash('ไม่สามารถสร้างบัญชีได้ เนื่องจากใบสมัครยังไม่ได้รับการอนุมัติ', 'danger')
        return redirect(url_for('registration.application_detail', application_id=application_id))
    
    # ตรวจสอบว่าสร้างบัญชีไปแล้วหรือไม่
    if application.is_converted_to_student:
        flash('บัญชีนักเรียนถูกสร้างไปแล้ว', 'warning')
        return redirect(url_for('registration.application_detail', application_id=application_id))
    
    # ตรวจสอบว่ามีบัญชีที่ใช้ citizen_id นี้อยู่แล้วหรือไม่
    existing_user = User.query.filter_by(citizen_id=application.citizen_id).first()
    if existing_user:
        flash(f'มีบัญชีที่ใช้เลขประจำตัวประชาชนนี้อยู่แล้ว ({existing_user.first_name} {existing_user.last_name})', 'danger')
        return redirect(url_for('registration.application_detail', application_id=application_id))
    
    try:
        # สร้างบัญชีผู้ใช้
        new_user = User(
            citizen_id=application.citizen_id,
            first_name=application.first_name,
            last_name=application.last_name,
            gender=application.gender,
            role='student',
            email=application.guardian_email,
            phone=application.guardian_phone,
            address=f"{application.guardian_address_no} {application.guardian_sub_district} {application.guardian_district} {application.guardian_province} {application.guardian_postal_code}"
        )
        
        # ตั้งรหัสผ่านเริ่มต้น (เลขประจำตัวประชาชน 4 ตัวสุดท้าย)
        default_password = application.citizen_id[-4:]
        new_user.set_password(default_password)
        
        db.session.add(new_user)
        db.session.flush()  # เพื่อให้ได้ ID ของ user
        
        # สร้าง StudentProfile
        student_id = f"S{application.admission_period.academic_year % 100}{application.admission_period.grade_level}{new_user.id:04d}"
        
        new_student_profile = StudentProfile(
            user_id=new_user.id,
            student_id=student_id,
            full_name_th=f"{application.first_name} {application.last_name}",
            full_name_en="",  # อาจจะไม่มีข้อมูลนี้ในใบสมัคร
            birth_date=application.birth_date,
            nationality=application.nationality,
            blood_type=application.blood_type,
            birth_province=application.birth_province,
            birth_other=application.birth_other,
            parent_status=application.guardian_status,
            disability=application.disability,
            special_talent=application.special_talent
        )
        
        db.session.add(new_student_profile)
        db.session.flush()
        
        # สร้าง GuardianProfile
        new_guardian = GuardianProfile(
            student_id=new_student_profile.id,
            full_name=application.guardian_full_name,
            nationality=application.guardian_nationality,
            status=application.guardian_status,
            occupation=application.guardian_occupation,
            position=application.guardian_position,
            workplace=application.guardian_workplace,
            income=application.guardian_income,
            address_no=application.guardian_address_no,
            moo=application.guardian_moo,
            soi=application.guardian_soi,
            road=application.guardian_road,
            sub_district=application.guardian_sub_district,
            district=application.guardian_district,
            province=application.guardian_province,
            postal_code=application.guardian_postal_code,
            phone=application.guardian_phone,
            email=application.guardian_email
        )
        
        db.session.add(new_guardian)
        
        # อัปเดตสถานะใบสมัคร
        application.is_converted_to_student = True
        
        db.session.commit()
        
        flash(f'สร้างบัญชีนักเรียนสำเร็จ (รหัสนักเรียน: {student_id}, รหัสผ่าน: {default_password})', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
    
    return redirect(url_for('registration.application_detail', application_id=application_id))

@registration_bp.route('/admin/applications/assign-classroom/<int:application_id>', methods=['POST'])
@login_required
@admin_required
def assign_classroom(application_id):
    """กำหนดห้องเรียนให้นักเรียนที่สอบผ่าน"""
    application = StudentApplication.query.get_or_404(application_id)
    classroom_id = request.form.get('classroom_id')
    
    # ตรวจสอบว่าสร้างบัญชีนักเรียนแล้วหรือไม่
    if not application.is_converted_to_student:
        flash('กรุณาสร้างบัญชีนักเรียนก่อนกำหนดห้องเรียน', 'danger')
        return redirect(url_for('registration.application_detail', application_id=application_id))
    
    # หาบัญชีนักเรียนที่สร้างจากใบสมัครนี้
    student = User.query.filter_by(citizen_id=application.citizen_id, role='student').first()
    
    if not student:
        flash('ไม่พบบัญชีนักเรียนที่เชื่อมโยงกับใบสมัครนี้', 'danger')
        return redirect(url_for('registration.application_detail', application_id=application_id))
    
    try:
        # ตรวจสอบว่านักเรียนอยู่ในห้องเรียนนี้แล้วหรือไม่
        existing_enrollment = ClassroomStudents.query.filter_by(
            classroom_id=classroom_id,
            student_id=student.id
        ).first()
        
        if existing_enrollment:
            flash('นักเรียนอยู่ในห้องเรียนนี้แล้ว', 'warning')
        else:
            # เพิ่มนักเรียนเข้าห้องเรียน
            new_enrollment = ClassroomStudents(
                classroom_id=classroom_id,
                student_id=student.id
            )
            db.session.add(new_enrollment)
            db.session.commit()
            flash('กำหนดห้องเรียนสำเร็จ', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
    
    return redirect(url_for('registration.application_detail', application_id=application_id))


@registration_bp.route('/admin/exam-rooms/delete/<int:room_id>', methods=['POST'])
@login_required
@admin_required
def delete_exam_room(room_id):
    """ลบห้องสอบ"""
    try:
        room = ExamRoom.query.get_or_404(room_id)

        # ตรวจสอบว่ามีผู้สมัครที่เชื่อมโยงกับห้องสอบนี้หรือไม่
        if room.applications:
            flash('ไม่สามารถลบห้องสอบนี้ได้ เนื่องจากมีผู้สมัครที่เชื่อมโยงอยู่', 'danger')
            return redirect(url_for('registration.admin_exam_rooms'))

        db.session.delete(room)
        db.session.commit()

        flash('ลบห้องสอบสำเร็จ', 'success')
        return redirect(url_for('registration.admin_exam_rooms'))

    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        return redirect(url_for('registration.admin_exam_rooms'))
