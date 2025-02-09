from flask import Blueprint, render_template, session, flash, redirect, url_for,request
from functools import wraps
from models.user import User
from flask import send_file
import pdfkit


from models.subject import Grade
student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'student':
            flash("Student only!", 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/student/home')
@student_required
def student_home():
    return render_template('student/student_home.html')




@student_bp.route('/student/grades', methods=['GET'])
def student_grades():
    """แสดงเกรดของนักเรียนและคำนวณ GPA"""
    student_id = session.get('user_id')

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    grades = Grade.query.filter_by(student_id=student_id).order_by(Grade.academic_year, Grade.grade_level).all()

    available_years = sorted(set(grade.academic_year for grade in grades))
    available_levels = sorted(set(grade.grade_level for grade in grades))

    selected_year = request.args.get('year', default=max(available_years) if available_years else None, type=int)
    selected_level = request.args.get('level', default=max(available_levels) if available_levels else None, type=int)
    selected_semester = request.args.get('semester', default=1, type=int)

    filtered_grades = Grade.query.filter_by(
        student_id=student_id,
        academic_year=selected_year,
        grade_level=selected_level,
        semester=selected_semester
    ).all()

    # **📌 คำนวณเกรดเฉลี่ย (GPA)**
    total_credits = sum(grade.subject.credits for grade in filtered_grades if grade.grade is not None)
    total_weighted_score = sum(grade.grade * grade.subject.credits for grade in filtered_grades if grade.grade is not None)
    gpa = round(total_weighted_score / total_credits, 2) if total_credits > 0 else None

    return render_template(
        'student/grades.html',
        student=student,
        grades=filtered_grades,
        available_years=available_years,
        available_levels=available_levels,
        selected_year=selected_year,
        selected_level=selected_level,
        selected_semester=selected_semester,
        gpa=gpa  # ส่งค่า GPA ไปยัง Template
    )


@student_bp.route('/student/grades/download', methods=['GET'])
def download_grades_pdf():
    """สร้าง PDF สำหรับเกรดที่เลือก"""
    student_id = session.get('user_id')

    # รับค่าปี, ชั้น และเทอมจาก URL
    selected_year = request.args.get('year', type=int)
    selected_level = request.args.get('level', type=int)
    selected_semester = request.args.get('semester', type=int)

    # ดึงข้อมูลเกรด
    grades = Grade.query.filter_by(
        student_id=student_id,
        academic_year=selected_year,
        grade_level=selected_level,
        semester=selected_semester
    ).all()

    # สร้าง HTML สำหรับ PDF
    html = render_template('student/grades_pdf.html', grades=grades, selected_year=selected_year)

    # แปลงเป็น PDF
    pdf = pdfkit.from_string(html, False)

    return send_file(
        pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"grades_{selected_year}.pdf"
    )