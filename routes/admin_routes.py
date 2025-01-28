from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from functools import wraps
from database import db
from models.user import User
from models.academic import AcademicSettings
from models.classroom import Classroom, ClassroomStudents
from models.subject import Subject
from models.subject import Subject, ClassroomSubjects
admin_bp = Blueprint('admin', __name__)


    
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Admin only!", 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/create_user', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        citizen_id = request.form.get('citizen_id')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        gender = request.form.get('gender')
        role = request.form.get('role')  # 'admin' / 'teacher' / 'student'
        education_level = request.form.get('education_level')  # รับค่า education_level

        # ตรวจว่ามี user นี้อยู่แล้วหรือไม่
        if User.query.filter_by(citizen_id=citizen_id).first():
            flash("User already exists.", 'error')
            return redirect(url_for('admin.create_user'))

        if role == 'student' and not education_level:
            flash("Education level is required for students.", 'error')
            return redirect(url_for('admin.create_user'))

        new_user = User(
            citizen_id=citizen_id,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            role=role,
            education_level=education_level if role == 'student' else None
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("User created successfully", 'success')
        return redirect(url_for('admin.create_user'))

    return render_template('admin/create_user.html')


@admin_bp.route('/admin/academic_settings', methods=['GET', 'POST'])
@admin_required
def academic_settings():
    setting = AcademicSettings.query.first()
    if request.method == 'POST':
        year = request.form.get('current_year')
        sem = request.form.get('current_semester')
        if not setting:
            setting = AcademicSettings(current_year=year, current_semester=sem)
            db.session.add(setting)
        else:
            setting.current_year = year
            setting.current_semester = sem
        db.session.commit()
        flash("Academic settings updated.", 'success')
        return redirect(url_for('admin.academic_settings'))

    return render_template('admin/academic_settings.html', setting=setting)

@admin_bp.route('/admin/create_classroom', methods=['GET', 'POST'])
@admin_required
def create_classroom():
    # ใช้ AcademicSettings ปัจจุบันเป็นค่า default
    setting = AcademicSettings.query.first()
    if request.method == 'POST':
        name = request.form.get('name')
        education_level = request.form.get('education_level')  # "primary" / "secondary"
        grade_level = request.form.get('grade_level')
        teacher_id = request.form.get('teacher_id')

        classroom = Classroom(
            name=name,
            education_level=education_level,
            grade_level=int(grade_level),
            academic_year=setting.current_year ,
            semester=setting.current_semester ,
            teacher_id=int(teacher_id) if teacher_id else None
        )
        db.session.add(classroom)
        db.session.commit()
        flash("Classroom created.", 'success')
        return redirect(url_for('admin.create_classroom'))

    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin/create_classroom.html', teachers=teachers)

@admin_bp.route('/admin/classrooms/<int:classroom_id>/add_student', methods=['GET', 'POST'])
@admin_required
def add_student_to_classroom(classroom_id):
    # ดึงข้อมูลห้องตาม id
    classroom = Classroom.query.get_or_404(classroom_id)

    if request.method == 'POST':
        student_id = request.form.get('student_id')

        # ตรวจสอบว่านักเรียนคนนี้อยู่ในห้องเรียนอื่นอยู่แล้วหรือไม่
        existing_entry = ClassroomStudents.query.filter_by(student_id=student_id).first()

        if existing_entry:
            flash("This student is already assigned to another classroom.", 'error')
        else:
            # เพิ่มนักเรียนเข้าห้องเรียน
            cs = ClassroomStudents(
                classroom_id=classroom.id,
                student_id=int(student_id)
            )
            db.session.add(cs)
            db.session.commit()
            flash("Student added to classroom successfully.", 'success')

        # เพิ่มเสร็จแล้ว redirect กลับไปหน้า detail ของห้อง
        return redirect(url_for('admin.classroom_detail', classroom_id=classroom.id))

    # ถ้าเป็น GET ให้ render ฟอร์ม
    # ดึงเฉพาะนักเรียนที่ยังไม่มีห้องเรียน
    students_in_classrooms = db.session.query(ClassroomStudents.student_id).subquery()
    available_students = User.query.filter_by(role='student') \
        .filter(~User.id.in_(students_in_classrooms)).all()

    return render_template(
        'admin/add_student_to_classroom.html', 
        classroom=classroom, 
        students=available_students
    )



@admin_bp.route('/admin/upgrade_classrooms')
@admin_required
def upgrade_classrooms():
    # ตัวอย่าง logic อย่างง่าย
    classrooms = Classroom.query.all()
    for cls in classrooms:
        # ตัวอย่าง: ถ้า grade_level < 6 => grade_level+1, อื่น ๆ ค่อยออกแบบเอง
        if cls.grade_level < 6:
            cls.grade_level += 1
    db.session.commit()
    flash("All classrooms upgraded (where possible).", 'success')
    return redirect(url_for('admin.create_classroom'))


# 1. หน้าแสดงห้องเรียนทั้งหมด
@admin_bp.route('/admin/classrooms', methods=['GET', 'POST'])
@admin_required
def list_classrooms():
    search_query = request.form.get('search')  # ค้นหาห้องเรียน
    if search_query:
        classrooms = Classroom.query.filter(Classroom.name.contains(search_query)).all()
    else:
        classrooms = Classroom.query.all()
    return render_template('admin/classrooms.html', classrooms=classrooms)

# 2. หน้าแสดงรายละเอียดห้องเรียน
@admin_bp.route('/admin/classrooms/<int:classroom_id>')
@admin_required
def classroom_detail(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    students = User.query.join(ClassroomStudents).filter(ClassroomStudents.classroom_id == classroom.id).all()
    subjects = Subject.query.join(ClassroomSubjects).filter(ClassroomSubjects.classroom_id == classroom.id).all()
    teachers = User.query.filter_by(role='teacher').all()
    return render_template(
        'admin/classroom_detail.html',
        classroom=classroom,
        students=students,
        subjects=subjects,
        teachers=teachers
    )
@admin_bp.route('/admin/classrooms/<int:classroom_id>/remove-subject/<int:subject_id>', methods=['POST'])
@admin_required
def remove_subject_from_classroom(classroom_id, subject_id):
    entry = ClassroomSubjects.query.filter_by(classroom_id=classroom_id, subject_id=subject_id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash('Subject removed from classroom.', 'success')
    return redirect(url_for('admin.classroom_detail', classroom_id=classroom_id))

@admin_bp.route('/admin/classrooms/<int:classroom_id>/remove-student/<int:student_id>', methods=['POST'])
@admin_required
def remove_student_from_classroom(classroom_id, student_id):
    # ตรวจสอบว่าห้องเรียนและนักเรียนมีอยู่ในห้องเรียนนั้น
    entry = ClassroomStudents.query.filter_by(classroom_id=classroom_id, student_id=student_id).first_or_404()
    db.session.delete(entry)
    db.session.commit()

    flash("Student has been removed from the classroom.", "success")
    return redirect(url_for('admin.classroom_detail', classroom_id=classroom_id))

# 3. แก้ไขชื่อห้องเรียน
@admin_bp.route('/admin/classrooms/<int:classroom_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_classroom(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    if request.method == 'POST':
        new_name = request.form.get('name')
        classroom.name = new_name
        db.session.commit()
        flash('Classroom name updated.', 'success')
        return redirect(url_for('admin.classroom_detail', classroom_id=classroom.id))
    return render_template('admin/edit_classroom.html', classroom=classroom)

# 4. ลบห้องเรียน
@admin_bp.route('/admin/classrooms/<int:classroom_id>/delete', methods=['POST'])
@admin_required
def delete_classroom(classroom_id):
    # ดึงข้อมูลห้องเรียน
    classroom = Classroom.query.get_or_404(classroom_id)

    # ลบข้อมูลในตารางที่เชื่อมโยงกับห้องเรียนนี้
    ClassroomStudents.query.filter_by(classroom_id=classroom.id).delete()

    # ลบห้องเรียน
    db.session.delete(classroom)
    db.session.commit()

    flash(f"Classroom '{classroom.name}' and its related data have been deleted.", 'success')
    return redirect(url_for('admin.list_classrooms'))


# 5. ตั้ง/เปลี่ยนครูผู้ดูแลห้องเรียน
@admin_bp.route('/admin/classrooms/<int:classroom_id>/assign-teacher', methods=['POST'])
@admin_required
def assign_teacher(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    teacher_id = request.form.get('teacher_id')
    if teacher_id:
        classroom.teacher_id = teacher_id
    else:
        classroom.teacher_id = None  # กรณีลบครูผู้ดูแล
    db.session.commit()
    flash('Teacher assignment updated.', 'success')
    return redirect(url_for('admin.classroom_detail', classroom_id=classroom.id))







@admin_bp.route('/admin/classrooms/<int:classroom_id>/subjects', methods=['GET', 'POST'])
@admin_required
def admin_classroom_subjects(classroom_id):
    """
    สำหรับ Admin: เพิ่ม/ลบ วิชาในห้องเรียนใดก็ได้
    """
    classroom = Classroom.query.get_or_404(classroom_id)

    if request.method == 'POST':
        subject_ids = request.form.getlist('subject_ids')
        for s_id in subject_ids:
            existing = ClassroomSubjects.query.filter_by(
                classroom_id=classroom.id, 
                subject_id=s_id
            ).first()
            if not existing:
                new_cs = ClassroomSubjects(classroom_id=classroom.id, subject_id=s_id)
                db.session.add(new_cs)
        db.session.commit()
        flash('เพิ่มรายวิชาในห้องเรียนสำเร็จ', 'success')
        return redirect(url_for('admin.admin_classroom_subjects', classroom_id=classroom.id))

    all_subjects = Subject.query.all()
    current_subject_ids = [cs.subject_id for cs in 
                           ClassroomSubjects.query.filter_by(classroom_id=classroom.id)]
    return render_template(
        'admin/classroom_subjects.html',
        classroom=classroom,
        all_subjects=all_subjects,
        current_subject_ids=current_subject_ids
    )

@admin_bp.route('/admin/classrooms/<int:classroom_id>/subjects/<int:subject_id>/delete', methods=['POST'])
@admin_required
def admin_remove_subject_from_classroom(classroom_id, subject_id):
    """
    สำหรับ Admin: ลบวิชาออกจากห้องเรียน
    """
    classroom = Classroom.query.get_or_404(classroom_id)
    association = ClassroomSubjects.query.filter_by(
        classroom_id=classroom.id, 
        subject_id=subject_id
    ).first_or_404()
    db.session.delete(association)
    db.session.commit()
    flash('ลบรายวิชาจากห้องเรียนสำเร็จ', 'success')
    return redirect(url_for('admin.admin_classroom_subjects', classroom_id=classroom.id))


@admin_bp.route('/admin/subjects', methods=['GET', 'POST'])
@admin_required
def admin_manage_subjects():
    """
    สร้าง/แสดงรายวิชา (Subjects) เฉพาะ Admin
    """
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        credits = request.form.get('credits')
        description = request.form.get('description')
        
        # เช็คว่ามี Subject code นี้แล้วหรือยัง
        if Subject.query.filter_by(code=code).first():
            flash('รหัสวิชานี้มีอยู่แล้ว', 'error')
            return redirect(url_for('admin.admin_manage_subjects'))
        
        # สร้าง subject ใหม่
        new_subject = Subject(
            code=code,
            name=name,
            credits=int(credits) if credits else 0,
            description=description
        )
        db.session.add(new_subject)
        db.session.commit()
        flash('สร้างรายวิชาสำเร็จ (Admin)', 'success')
        return redirect(url_for('admin.admin_manage_subjects'))
    
    # ถ้าเป็น GET ให้แสดงรายวิชาทั้งหมด
    subjects = Subject.query.all()
    return render_template('admin/manage_subjects.html', subjects=subjects)




@admin_bp.route('/admin/add_student_to_classroom_all', methods=['GET', 'POST'])
@admin_required
def add_student_to_classroom_all():
    if request.method == 'POST':
        classroom_id = request.form.get('classroom_id')
        student_id = request.form.get('student_id')

        # ตรวจสอบว่านักเรียนคนนี้อยู่ในห้องเรียนอื่นอยู่แล้วหรือไม่
        existing_entry = ClassroomStudents.query.filter_by(student_id=student_id).first()

        if existing_entry:
            flash("This student is already assigned to another classroom.", 'error')
        else:
            # เพิ่มนักเรียนเข้าห้องเรียน
            cs = ClassroomStudents(
                classroom_id=int(classroom_id),
                student_id=int(student_id)
            )
            db.session.add(cs)
            db.session.commit()
            flash("Student added to classroom successfully.", 'success')

        
        return redirect(url_for('admin.add_student_to_classroom'))

    classrooms = Classroom.query.all()
    # ดึงเฉพาะนักเรียนที่ยังไม่มีห้องเรียน
    students_in_classrooms = db.session.query(ClassroomStudents.student_id).subquery()
    available_students = User.query.filter_by(role='student').filter(
        ~User.id.in_(students_in_classrooms)
    ).all()
    return render_template('admin/add_student_to_classroom_all.html', classrooms=classrooms, students=available_students )

