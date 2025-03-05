from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from functools import wraps
from database import db
from models.user import User
from models.academic import AcademicSettings
from models.classroom import Classroom, ClassroomStudents
from models.subject import Subject
from models.subject import Subject, ClassroomSubjects, subject_teachers
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

        # ตรวจว่ามี user นี้อยู่แล้วหรือไม่
        if User.query.filter_by(citizen_id=citizen_id).first():
            flash("User already exists.", 'error')
            return redirect(url_for('admin.create_user'))

        new_user = User(
            citizen_id=citizen_id,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            role=role
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

# admin_routes.py

@admin_bp.route('/admin/create_classroom', methods=['GET', 'POST'])
@admin_required
def create_classroom():
    """สร้างห้องเรียน โดยตั้งชื่อห้องอัตโนมัติ"""
    setting = AcademicSettings.query.first()
    if request.method == 'POST':
        education_level_input = request.form.get('education_level')
        grade_level = request.form.get('grade_level')
        room_number = request.form.get('room_number')
        teacher_id = request.form.get('teacher_id')

        # แปลง education_level เป็นภาษาไทย
        if education_level_input == 'primary':
            education_level = 'ประถมศึกษา'
            prefix = 'ป.'
        elif education_level_input == 'secondary':
            education_level = 'มัธยมศึกษา'
            prefix = 'ม.'
        else:
            education_level = education_level_input
            prefix = ''

        # **สร้างชื่อห้องอัตโนมัติ**
        auto_name = f"{prefix}{grade_level}/{room_number}"

        classroom = Classroom(
            name=auto_name,
            education_level=education_level,
            grade_level=int(grade_level),
            room_number=int(room_number),
            creation_year=setting.current_year,
            semester=setting.current_semester,
            teacher_id=int(teacher_id) if teacher_id else None
        )

        db.session.add(classroom)
        db.session.commit()
        flash("Classroom created successfully.", 'success')
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



@admin_bp.route('/admin/upgrade_classrooms', methods=['GET', 'POST'])
@admin_required
def upgrade_classrooms():
    """หน้าอัปเกรดห้องเรียน แสดงเฉพาะห้องที่ยังสามารถอัปเกรดได้"""
    if request.method == 'POST':
        selected_classrooms = request.form.getlist('classroom_ids')  # รับค่าห้องเรียนที่เลือก

        for class_id in selected_classrooms:
            classroom = Classroom.query.get(class_id)
            if classroom and classroom.grade_level < 7:
                classroom.grade_level += 1
                # อัปเดตชื่อห้องเรียนใหม่ (เช่น ป.1/1 → ป.2/1)
                prefix = 'ป.' if classroom.education_level == 'ประถมศึกษา' else 'ม.'
                classroom.name = f"{prefix}{classroom.grade_level}/{classroom.room_number}"

        db.session.commit()
        flash("อัปเกรดห้องเรียนสำเร็จ!", 'success')
        return redirect(url_for('admin.upgrade_classrooms'))

    # ดึงเฉพาะห้องที่ยังสามารถอัปเกรดได้ (grade_level < 7)
    classrooms = Classroom.query.filter(Classroom.grade_level < 7).all()
    return render_template('admin/upgrade_classrooms.html', classrooms=classrooms)


# 1. หน้าแสดงห้องเรียนทั้งหมด
@admin_bp.route('/admin/classrooms', methods=['GET', 'POST'])
@admin_required
def list_classrooms():
    search_query = request.form.get('search')
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
        teachers=teachers,
        creation_year=classroom.creation_year  # ส่งค่า creation_year ไปยัง template
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
    """ให้ Admin สามารถแก้ไขข้อมูลห้องเรียน และอัปเดตชื่อห้องอัตโนมัติ"""
    classroom = Classroom.query.get_or_404(classroom_id)

    if request.method == 'POST':
        education_level_input = request.form.get('education_level')
        grade_level = request.form.get('grade_level')
        room_number = request.form.get('room_number')
        teacher_id = request.form.get('teacher_id')

        # แปลง Education Level
        if education_level_input == 'primary':
            education_level = 'ประถมศึกษา'
            prefix = 'ป.'
        elif education_level_input == 'secondary':
            education_level = 'มัธยมศึกษา'
            prefix = 'ม.'
        else:
            education_level = education_level_input
            prefix = ''

        # อัปเดตค่าต่าง ๆ
        classroom.education_level = education_level
        classroom.grade_level = int(grade_level)
        classroom.room_number = int(room_number)
        classroom.teacher_id = int(teacher_id) if teacher_id else None

        # **อัปเดตชื่อห้องอัตโนมัติ**
        classroom.name = f"{prefix}{classroom.grade_level}/{classroom.room_number}"

        db.session.commit()
        flash('แก้ไขข้อมูลห้องเรียนสำเร็จ', 'success')
        return redirect(url_for('admin.classroom_detail', classroom_id=classroom.id))

    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin/edit_classroom.html', classroom=classroom, teachers=teachers)

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
    แอดมินสามารถเพิ่ม/ลบ รายวิชาในห้องเรียน และกำหนดครูที่สอนวิชานั้นๆ ได้
    """
    classroom = Classroom.query.get_or_404(classroom_id)

    if request.method == 'POST':
        subject_ids = request.form.getlist('subject_ids')
        
        for subject_id in subject_ids:
            existing = ClassroomSubjects.query.filter_by(
                classroom_id=classroom.id, 
                subject_id=subject_id
            ).first()

            if not existing:
                assigned_teacher = request.form.get(f'teacher_for_{subject_id}')
                new_cs = ClassroomSubjects(
                    classroom_id=classroom.id, 
                    subject_id=subject_id, 
                    teacher_id=assigned_teacher if assigned_teacher else None
                )
                db.session.add(new_cs)

        db.session.commit()
        flash('เพิ่มรายวิชาในห้องเรียนสำเร็จ', 'success')
        return redirect(url_for('admin.admin_classroom_subjects', classroom_id=classroom.id))

    all_subjects = Subject.query.all()

    # ✅ ดึงเฉพาะครูที่สามารถสอนแต่ละรายวิชา
    subject_teachers_mapping = {
        subject.id: User.query.join(subject_teachers)
                              .filter(subject_teachers.c.subject_id == subject.id)
                              .all()
        for subject in all_subjects
    }

    current_subjects = ClassroomSubjects.query.filter_by(classroom_id=classroom.id).all()

    return render_template(
        'admin/classroom_subjects.html',
        classroom=classroom,
        all_subjects=all_subjects,
        subject_teachers_mapping=subject_teachers_mapping,
        current_subjects=current_subjects
    )

@admin_bp.route('/admin/classrooms/<int:classroom_id>/subjects/update_teachers', methods=['POST'])
@admin_required
def update_subject_teachers(classroom_id):
    """อัปเดตครูผู้สอนของรายวิชาในห้องเรียน"""
    classroom = Classroom.query.get_or_404(classroom_id)

    # วนลูปตรวจสอบค่าที่ส่งมาใน request.form
    for key, value in request.form.items():
        if key.startswith("teacher_for_"):  # ค้นหา input ที่เป็น teacher_for_
            subject_id = int(key.replace("teacher_for_", ""))  # แปลง subject_id จาก key

            classroom_subject = ClassroomSubjects.query.filter_by(
                classroom_id=classroom.id, subject_id=subject_id
            ).first()

            if classroom_subject:
                if value:  # ถ้ามีค่า teacher_id
                    classroom_subject.teacher_id = int(value)
                else:
                    classroom_subject.teacher_id = None  # ถ้าเลือก "ไม่ระบุ"

    db.session.commit()
    flash('อัปเดตครูผู้สอนเรียบร้อย', 'success')
    return redirect(url_for('admin.admin_classroom_subjects', classroom_id=classroom.id))


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


@admin_bp.route('/admin/classrooms/<int:classroom_id>/subjects/<int:subject_id>/assign-teacher', methods=['POST'])
@admin_required
def assign_teacher_to_subject(classroom_id, subject_id):
    """ให้แอดมินเปลี่ยนครูที่สอนวิชาในห้องเรียน"""
    classroom_subject = ClassroomSubjects.query.filter_by(classroom_id=classroom_id, subject_id=subject_id).first_or_404()
    
    teacher_id = request.form.get('teacher_id')
    if teacher_id == "none":
        classroom_subject.teacher_id = None
    else:
        classroom_subject.teacher_id = int(teacher_id)
    
    db.session.commit()
    flash("อัปเดตครูผู้สอนสำเร็จ", "success")
    return redirect(url_for('admin.admin_classroom_subjects', classroom_id=classroom_id))
