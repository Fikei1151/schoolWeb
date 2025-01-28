# routes/subject_routes.py (หรือ admin_routes/teacher_routes ถ้าต้องการแยก)

from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from functools import wraps
from database import db
from models.user import User
from models.subject import Subject

subject_bp = Blueprint('subject', __name__)

def admin_or_teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role')
        if role not in ['admin','teacher']:
            flash("Only admin or teacher can access this page.", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@subject_bp.route('/subjects')
@admin_or_teacher_required
def list_subjects():
    """หน้าแสดงรายวิชาทั้งหมด"""
    subjects = Subject.query.all()
    return render_template('subject/subjects_list.html', subjects=subjects)


@subject_bp.route('/subjects/<int:subject_id>')
@admin_or_teacher_required
def subject_detail(subject_id):
    """หน้าแสดงรายละเอียดรายวิชา และปุ่มแก้ไข ถ้าเจ้าของหรือ admin"""
    subject = Subject.query.get_or_404(subject_id)
    
    # เช็กว่าคนปัจจุบันเป็นเจ้าของ (subject.owner) หรือเป็น admin
    can_edit = False
    current_user_id = session.get('user_id')
    current_role = session.get('role')

    if current_role == 'admin':
        can_edit = True
    else:
        # ถ้า role = teacher => เช็คว่า user_id == subject.created_by
        if subject.created_by == current_user_id:
            can_edit = True

    return render_template('subject/subject_detail.html', subject=subject, can_edit=can_edit)
@subject_bp.route('/subjects/<int:subject_id>/edit', methods=['GET','POST'])
@admin_or_teacher_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    # ตรวจสอบสิทธิ์
    current_user_id = session.get('user_id')
    current_role = session.get('role')

    if not (current_role == 'admin' or subject.created_by == current_user_id):
        flash("คุณไม่มีสิทธิ์แก้ไขรายวิชานี้", "error")
        return redirect(url_for('subject.subject_detail', subject_id=subject.id))

    if request.method == 'POST':
        subject.code = request.form.get('code')
        subject.name = request.form.get('name')
        subject.credits = int(request.form.get('credits', 0))
        subject.description = request.form.get('description')
        db.session.commit()
        flash("แก้ไขรายวิชาสำเร็จ", "success")
        return redirect(url_for('subject.subject_detail', subject_id=subject.id))

    return render_template('subject/edit_subject.html', subject=subject)


@subject_bp.route('/subjects/<int:subject_id>/add_teacher', methods=['GET','POST'])
@admin_or_teacher_required
def add_teacher(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    # ตรวจสอบสิทธิ์
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    if not (current_role == 'admin' or subject.created_by == current_user_id):
        flash("คุณไม่มีสิทธิ์จัดการครูผู้สอนในรายวิชานี้", "error")
        return redirect(url_for('subject.subject_detail', subject_id=subject.id))

    if request.method == 'POST':
        teacher_ids = request.form.getlist('teacher_ids')  # รับทีละหลายคน
        for t_id in teacher_ids:
            # หา user ที่ role=teacher เท่านั้น
            teacher_user = User.query.filter_by(id=t_id, role='teacher').first()
            if teacher_user and teacher_user not in subject.teachers:
                subject.teachers.append(teacher_user)
        db.session.commit()
        flash("เพิ่มครูผู้สอนสำเร็จ", "success")
        return redirect(url_for('subject.subject_detail', subject_id=subject.id))

    # ดึง teacher ทั้งหมด (หรือจะกรอง teacher ที่ยังไม่ได้สอนวิชานี้ก็ได้)
    all_teachers = User.query.filter_by(role='teacher').all()
    return render_template('subject/add_teacher.html', subject=subject, all_teachers=all_teachers)

@subject_bp.route('/subjects/<int:subject_id>/remove_teacher/<int:teacher_id>', methods=['POST'])
@admin_or_teacher_required
def remove_teacher(subject_id, teacher_id):
    subject = Subject.query.get_or_404(subject_id)

    # ตรวจสอบสิทธิ์
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    if not (current_role == 'admin' or subject.created_by == current_user_id):
        flash("คุณไม่มีสิทธิ์จัดการครูผู้สอนในรายวิชานี้", "error")
        return redirect(url_for('subject.subject_detail', subject_id=subject.id))

    teacher_user = User.query.filter_by(id=teacher_id, role='teacher').first_or_404()
    if teacher_user in subject.teachers:
        subject.teachers.remove(teacher_user)
        db.session.commit()
        flash("ลบครูผู้สอนออกจากรายวิชาแล้ว", "success")
    else:
        flash("ไม่พบครูคนนี้ในรายวิชานี้", "error")

    return redirect(url_for('subject.subject_detail', subject_id=subject.id))
