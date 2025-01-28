from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from functools import wraps
from database import db
from models.user import User
from models.classroom import Classroom, ClassroomStudents
from models.subject import Subject, ClassroomSubjects,Grade
teacher_bp = Blueprint('teacher', __name__)

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'teacher':
            flash("Teacher only!", 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/teacher/home')
@teacher_required
def teacher_home():
    return render_template('teacher/teacher_home.html')



# 1. หน้าแสดงห้องเรียนที่ครูดูแล
@teacher_bp.route('/teacher/classrooms')
@teacher_required
def list_classrooms():
    teacher_id = session.get('user_id')  # ID ของครูที่ล็อกอินอยู่
    classrooms = Classroom.query.filter_by(teacher_id=teacher_id).all()
    return render_template('teacher/classrooms.html', classrooms=classrooms)

# 2. หน้าแสดงรายละเอียดห้องเรียน (เฉพาะห้องที่ครูดูแล)
# ใน teacher_routes.py, ฟังก์ชัน classroom_detail
@teacher_bp.route('/teacher/classrooms/<int:classroom_id>')
@teacher_required
def classroom_detail(classroom_id):
    teacher_id = session.get('user_id')
    classroom = Classroom.query.filter_by(id=classroom_id, teacher_id=teacher_id).first_or_404()

    # ดึงนักเรียนที่อยู่ในห้องเรียนนี้
    students = User.query.join(ClassroomStudents).filter(ClassroomStudents.classroom_id == classroom.id).all()

    # ดึงนักเรียนทั้งหมดที่ยังไม่ได้อยู่ในห้องเรียนใด ๆ
    students_in_classrooms = db.session.query(ClassroomStudents.student_id).subquery()
    available_students = User.query.filter_by(role='student').filter(
        ~User.id.in_(students_in_classrooms)
    ).all()

    # ดึงรายวิชาที่เรียนในห้องนี้
    subjects = Subject.query.join(ClassroomSubjects).filter(ClassroomSubjects.classroom_id == classroom.id).all()

    return render_template(
        'teacher/classroom_detail.html',
        classroom=classroom,
        students=students,
        available_students=available_students,
        subjects=subjects
    )

# 3. แก้ไขชื่อห้องเรียน (เฉพาะห้องที่ครูดูแล)
@teacher_bp.route('/teacher/classrooms/<int:classroom_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_classroom(classroom_id):
    teacher_id = session.get('user_id')
    classroom = Classroom.query.filter_by(id=classroom_id, teacher_id=teacher_id).first_or_404()
    if request.method == 'POST':
        new_name = request.form.get('name')
        classroom.name = new_name
        db.session.commit()
        flash('Classroom name updated.', 'success')
        return redirect(url_for('teacher.classroom_detail', classroom_id=classroom.id))
    return render_template('teacher/edit_classroom.html', classroom=classroom)

# 4. เชิญนักเรียนเข้าห้องเรียน (เฉพาะห้องที่ครูดูแล)
# ใน teacher_routes.py, ฟังก์ชัน invite_student
@teacher_bp.route('/teacher/classrooms/<int:classroom_id>/invite-student', methods=['POST'])
@teacher_required
def invite_student(classroom_id):
    teacher_id = session.get('user_id')
    classroom = Classroom.query.filter_by(id=classroom_id, teacher_id=teacher_id).first_or_404()

    student_id = request.form.get('student_id')

    # ตรวจสอบว่านักเรียนอยู่ในห้องเรียนอื่นอยู่แล้วหรือไม่
    existing_entry = ClassroomStudents.query.filter_by(student_id=student_id).first()

    if existing_entry:
        flash("นักเรียนนี้อยู่ในห้องเรียนอื่นแล้ว", 'error')
    else:
        # เพิ่มนักเรียนเข้าห้องเรียน
        new_entry = ClassroomStudents(classroom_id=classroom.id, student_id=student_id)
        db.session.add(new_entry)
        db.session.commit()
        flash("เพิ่มนักเรียนเข้าห้องเรียนสำเร็จ", 'success')

    return redirect(url_for('teacher.classroom_detail', classroom_id=classroom.id))

@teacher_bp.route('/teacher/classrooms/<int:classroom_id>/remove-student/<int:student_id>', methods=['POST'])
@teacher_required
def remove_student_from_classroom(classroom_id, student_id):
    teacher_id = session.get('user_id')

    # ตรวจสอบว่าห้องเรียนเป็นของครูคนนี้
    classroom = Classroom.query.filter_by(id=classroom_id, teacher_id=teacher_id).first_or_404()

    # ตรวจสอบว่านักเรียนอยู่ในห้องเรียน
    entry = ClassroomStudents.query.filter_by(classroom_id=classroom.id, student_id=student_id).first_or_404()

    # ลบนักเรียนออกจากห้องเรียน
    db.session.delete(entry)
    db.session.commit()

    flash("นักเรียนถูกลบออกจากห้องเรียนแล้ว", "success")
    return redirect(url_for('teacher.classroom_detail', classroom_id=classroom.id))







# เพิ่มเส้นทางสร้างรายวิชาสำหรับครู
@teacher_bp.route('/teacher/subjects', methods=['GET', 'POST'])
@teacher_required
def teacher_manage_subjects():
    """
    สร้าง/แสดงรายวิชา (Subjects) เฉพาะ Teacher
    """
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        credits = request.form.get('credits')
        description = request.form.get('description')
        creator_id = session.get('user_id')
        # เช็คว่ามี Subject code นี้แล้วหรือยัง
        if Subject.query.filter_by(code=code).first():
            flash('รหัสวิชานี้มีอยู่แล้ว', 'error')
            return redirect(url_for('teacher.teacher_manage_subjects'))
        
        # สร้าง subject ใหม่
        new_subject = Subject(
            code=code,
            name=name,
            credits=int(credits) if credits else 0,
            description=description,
            created_by=creator_id
        )
        db.session.add(new_subject)
        db.session.commit()
        flash('สร้างรายวิชาสำเร็จ (Teacher)', 'success')
        return redirect(url_for('teacher.teacher_manage_subjects'))
    
    # ถ้าเป็น GET ให้แสดงรายวิชาทั้งหมด
    subjects = Subject.query.all()
    return render_template('teacher/manage_subjects.html', subjects=subjects)


# ปรับปรุงการจัดการรายวิชาในห้องเรียน
@teacher_bp.route('/teacher/classrooms/<int:classroom_id>/subjects', methods=['GET', 'POST'])
@teacher_required
def classroom_subjects(classroom_id):
    """ครูสามารถเพิ่มรายวิชาในห้องที่ตนเป็นผู้ดูแลเท่านั้น"""
    teacher_id = session.get('user_id')
    # ดึงห้องเรียนที่ teacher_id = ครูที่ล็อกอินอยู่
    classroom = Classroom.query.filter_by(id=classroom_id, teacher_id=teacher_id).first_or_404()
    
    if request.method == 'POST':
        # รับ subject_ids (รายวิชาที่ครูเลือกเพิ่ม)
        subject_ids = request.form.getlist('subject_ids')
        for subject_id in subject_ids:
            # ตรวจสอบว่ามีใน classroom_subjects แล้วหรือไม่
            existing = ClassroomSubjects.query.filter_by(classroom_id=classroom.id, subject_id=subject_id).first()
            if not existing:
                association = ClassroomSubjects(classroom_id=classroom.id, subject_id=subject_id)
                db.session.add(association)
        db.session.commit()
        flash('เพิ่มรายวิชาในห้องเรียนสำเร็จ', 'success')
        return redirect(url_for('teacher.classroom_subjects', classroom_id=classroom.id))
    
    # ดึงข้อมูลรายวิชาทั้งหมด
    all_subjects = Subject.query.all()
    # ดึงรายวิชาที่มีในห้องอยู่แล้ว (เป็น subject_id)
    current_subjects = [cs.subject_id for cs in ClassroomSubjects.query.filter_by(classroom_id=classroom.id).all()]

    return render_template('teacher/classroom_subjects.html',
                           classroom=classroom,
                           all_subjects=all_subjects,
                           current_subjects=current_subjects)

@teacher_bp.route('/teacher/classrooms/<int:classroom_id>/subjects/<int:subject_id>/delete', methods=['POST'])
@teacher_required
def remove_subject(classroom_id, subject_id):
    """ลบรายวิชาออกจากห้องเรียน (เฉพาะห้องที่ครูเป็นผู้ดูแล)"""
    teacher_id = session.get('user_id')
    classroom = Classroom.query.filter_by(id=classroom_id, teacher_id=teacher_id).first_or_404()
    
    association = ClassroomSubjects.query.filter_by(classroom_id=classroom.id, subject_id=subject_id).first_or_404()
    db.session.delete(association)
    db.session.commit()
    flash('ลบรายวิชาจากห้องเรียนสำเร็จ', 'success')
    return redirect(url_for('teacher.classroom_subjects', classroom_id=classroom.id))





@teacher_bp.route('/teacher/grade_management')
@teacher_required
def grade_management():
    """หน้าแสดงห้องเรียนที่ครูสอนและรายวิชาที่สอนในแต่ละห้อง"""
    teacher_id = session.get('user_id')
    
    # ดึงห้องเรียนที่ครูสอน
    classrooms = Classroom.query.filter_by(teacher_id=teacher_id).all()
    
    # ดึงรายวิชาที่ครูสอนในแต่ละห้องเรียน
    classroom_subjects = {}
    for classroom in classrooms:
        subjects = Subject.query.join(ClassroomSubjects).filter(ClassroomSubjects.classroom_id == classroom.id).all()
        classroom_subjects[classroom.id] = subjects
    
    return render_template('teacher/grade_management.html', classrooms=classrooms, classroom_subjects=classroom_subjects)

@teacher_bp.route('/teacher/grade_management/<int:classroom_id>/<int:subject_id>')
@teacher_required
def grade_students(classroom_id, subject_id):
    """หน้าแสดงรายชื่อนักเรียนในห้องเรียนและรายวิชาที่เลือก"""
    teacher_id = session.get('user_id')
    
    # ตรวจสอบว่าห้องเรียนและรายวิชาเป็นของครูที่ล็อกอินอยู่
    classroom = Classroom.query.filter_by(id=classroom_id, teacher_id=teacher_id).first_or_404()
    subject = Subject.query.filter_by(id=subject_id).first_or_404()
    
    # ดึงนักเรียนที่อยู่ในห้องเรียนนี้
    students = User.query.join(ClassroomStudents).filter(ClassroomStudents.classroom_id == classroom.id).all()
    
    return render_template('teacher/grade_students.html', classroom=classroom, subject=subject, students=students)

@teacher_bp.route('/teacher/grade_management/<int:classroom_id>/<int:subject_id>/enter_grades', methods=['GET', 'POST'])
@teacher_required
def enter_grades(classroom_id, subject_id):
    """หน้าป้อนเกรดสำหรับนักเรียนในห้องเรียนและรายวิชาที่เลือก"""
    teacher_id = session.get('user_id')
    
    # ตรวจสอบว่าห้องเรียนและรายวิชาเป็นของครูที่ล็อกอินอยู่
    classroom = Classroom.query.filter_by(id=classroom_id, teacher_id=teacher_id).first_or_404()
    subject = Subject.query.filter_by(id=subject_id).first_or_404()
    
    # ดึงนักเรียนที่อยู่ในห้องเรียนนี้
    students = User.query.join(ClassroomStudents).filter(ClassroomStudents.classroom_id == classroom.id).all()
    
    # ดึงเทอมและระดับชั้นปัจจุบันจากห้องเรียน
    term = f"{classroom.semester}/{classroom.academic_year}"  # เช่น "1/2568"
    grade_level = classroom.grade_level  # เช่น "ป.1"

    if request.method == 'POST':
        for student in students:
            grade_value = request.form.get(f'grade_{student.id}')
            if grade_value:
                # ดึงค่า education_level จาก user ของนักเรียน
                education_level = student.education_level

                # ตรวจสอบว่ามีเกรดอยู่แล้วหรือไม่
                grade = Grade.query.filter_by(
                    student_id=student.id, 
                    subject_id=subject_id, 
                    term=term, 
                    grade_level=grade_level
                ).first()
                if grade:
                    grade.grade = grade_value  # อัปเดตเกรดถ้ามีอยู่แล้ว
                else:
                    # เพิ่มเกรดใหม่ถ้ายังไม่มี
                    new_grade = Grade(
                        student_id=student.id,
                        subject_id=subject_id,
                        grade=grade_value,
                        term=term,
                        grade_level=grade_level,
                        education_level=education_level  # เพิ่มค่า education_level
                    )
                    db.session.add(new_grade)
        db.session.commit()
        flash('บันทึกเกรดสำเร็จ', 'success')
        return redirect(url_for('teacher.grade_students', classroom_id=classroom_id, subject_id=subject_id))
    
    # ดึงเกรดที่มีอยู่แล้ว (ถ้ามี) สำหรับแสดงผล
    grades = {grade.student_id: grade.grade for grade in Grade.query.filter_by(
        subject_id=subject_id, 
        term=term, 
        grade_level=grade_level
    ).all()}
    
    return render_template('teacher/enter_grades.html', classroom=classroom, subject=subject, students=students, grades=grades)
