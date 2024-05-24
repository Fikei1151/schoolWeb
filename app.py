from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from forms.contact_form import ContactForm
from forms.classroom_form import ClassroomForm
from forms.course_form import CourseForm
from forms.grade_form import GradeForm
from models.user import db, User
from models.classroom import Classroom
from models.course import Course
from models.grade import Grade
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from utils.decorators import admin_required, teacher_required, student_required
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_user_id(form.user_id.data)
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid user ID or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            user_id=form.user_id.data, 
            email=form.email.data, 
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('index'))

@app.route('/students')
@login_required
@student_required
def students():
    students = User.get_all_students()
    return render_template('students.html', students=students)

@app.route('/admin')
@login_required
@admin_required
def admin():
    return render_template('admin.html')

@app.route('/teacher_dashboard')
@login_required
@teacher_required
def teacher_dashboard():
    return render_template('dashboard.html')

@app.route('/student_dashboard')
@login_required
@student_required
def student_dashboard():
    return render_template('dashboard.html')

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        flash('Message sent successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('contact.html', form=form)

@app.route('/classrooms')
@login_required
@admin_required
def classrooms():
    classrooms = Classroom.get_all_classrooms()
    return render_template('classrooms.html', classrooms=classrooms)

@app.route('/classrooms/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_classroom():
    form = ClassroomForm()
    if form.validate_on_submit():
        print("Form validated successfully")  # ตรวจสอบว่าฟอร์มถูก validate
        print(f"Name: {form.name.data}, Academic Year: {form.academic_year.data}")  # พิมพ์ค่าเพื่อดูใน console
        new_classroom = Classroom(name=form.name.data, academic_year=form.academic_year.data)
        db.session.add(new_classroom)
        db.session.commit()
        flash('Classroom added successfully!', 'success')
        return redirect(url_for('classrooms'))
    else:
        print("Form validation failed")  # ตรวจสอบว่าฟอร์มไม่ผ่าน validation
        print(form.errors)  # พิมพ์ข้อผิดพลาดในฟอร์ม
        flash('Failed to add classroom. Please check the form.', 'danger')
    return render_template('add_classroom.html', form=form)

@app.route('/classrooms/edit/<int:classroom_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_classroom(classroom_id):
    classroom = Classroom.get_by_id(classroom_id)
    if not classroom:
        flash('Classroom not found', 'danger')
        return redirect(url_for('classrooms'))
    form = ClassroomForm(obj=classroom)
    if form.validate_on_submit():
        classroom.name = form.name.data
        classroom.academic_year = form.academic_year.data
        classroom.teacher_id = form.teacher_id.data
        db.session.commit()
        flash('Classroom updated successfully!', 'success')
        return redirect(url_for('classrooms'))
    return render_template('edit_classroom.html', form=form)

@app.route('/class_me')
@login_required
@teacher_required
def class_me():
    classroom = Classroom.query.filter_by(teacher_id=current_user.id).first()
    if not classroom:
        flash('You are not assigned to any classroom', 'danger')
        return redirect(url_for('index'))
    return redirect(url_for('grades_classroom', classroom_id=classroom.id))


@app.route('/classrooms/delete/<int:classroom_id>', methods=['POST'])
@login_required
@admin_required
def delete_classroom(classroom_id):
    success = Classroom.delete_classroom(classroom_id)
    if success:
        flash('Classroom deleted successfully', 'success')
    else:
        flash('Failed to delete classroom', 'danger')
    return redirect(url_for('classrooms'))
@app.route('/classrooms/<int:classroom_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def view_classroom(classroom_id):
    classroom = Classroom.get_by_id(classroom_id)
    if not classroom:
        flash('Classroom not found', 'danger')
        return redirect(url_for('classrooms'))
    
    courses_not_in_class = Course.query.filter(~Course.classrooms.any(id=classroom_id)).all()
    students_not_in_class = User.query.filter((User.classroom_id != classroom_id) | (User.classroom_id == None)).all()
    teachers = User.query.filter_by(role='teacher').all()
    
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        if teacher_id:
            classroom.teacher_id = teacher_id
            db.session.commit()
            flash('Teacher assigned to classroom successfully!', 'success')
        if student_id:
            student = db.session.get(User, student_id)
            if student and student.role == 'student':
                student.classroom_id = classroom_id
                db.session.commit()
                flash('Student added to classroom successfully!', 'success')
        if course_id:
            course = db.session.get(Course, course_id)
            if course:
                classroom.courses.append(course)
                db.session.commit()
                flash('Course added to classroom successfully!', 'success')
        return redirect(url_for('view_classroom', classroom_id=classroom_id))
    
    return render_template('view_classroom.html', classroom=classroom, students_not_in_class=students_not_in_class, courses_not_in_class=courses_not_in_class, teachers=teachers)

@app.route('/classrooms/<int:classroom_id>/remove_student/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def remove_student(classroom_id, student_id):
    student = db.session.get(User, student_id)
    if student and student.classroom_id == classroom_id:
        student.classroom_id = None
        db.session.commit()
        flash('Student removed from classroom successfully!', 'success')
    else:
        flash('Failed to remove student from classroom', 'danger')
    return redirect(url_for('view_classroom', classroom_id=classroom_id))

@app.route('/classrooms/<int:classroom_id>/remove_course/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def remove_course(classroom_id, course_id):
    course = db.session.get(Course, course_id)
    classroom = db.session.get(Classroom, classroom_id)
    if course and classroom:
        classroom.courses.remove(course)
        db.session.commit()
        flash('Course removed from classroom successfully!', 'success')
    else:
        flash('Failed to remove course from classroom', 'danger')
    return redirect(url_for('view_classroom', classroom_id=classroom_id))

@app.route('/courses', methods=['GET'])
@login_required
@admin_required
def courses():
    courses = Course.get_all_courses()
    return render_template('courses.html', courses=courses)


@app.route('/courses/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_course():
    form = CourseForm()
    if form.validate_on_submit():
        Course.add_course(name=form.name.data, code=form.code.data, credit=form.credit.data, description=form.description.data)
        flash('Course added successfully!', 'success')
        return redirect(url_for('courses'))
    else:
        flash('Failed to add course. Please check the form.', 'danger')
    return render_template('add_course.html', form=form)

@app.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.get_course_by_id(course_id)
    if not course:
        flash('Course not found', 'danger')
        return redirect(url_for('courses'))
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        Course.update_course(course_id=course_id, name=form.name.data, code=form.code.data, credit=form.credit.data, description=form.description.data)
        flash('Course updated successfully!', 'success')
        return redirect(url_for('courses'))
    return render_template('edit_course.html', form=form)

@app.route('/courses/delete/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    success = Course.delete_course(course_id)
    if success:
        flash('Course deleted successfully', 'success')
    else:
        flash('Failed to delete course', 'danger')
    return redirect(url_for('courses'))

@app.route('/classrooms/<int:classroom_id>/add_course', methods=['POST'])
@login_required
@admin_required
def add_course_to_classroom(classroom_id):
    course_id = request.form.get('course_id')
    course = db.session.get(Course, course_id)
    classroom = db.session.get(Classroom, classroom_id)
    if course and classroom:
        classroom.courses.append(course)
        db.session.commit()
        flash('Course added to classroom successfully!', 'success')
    else:
        flash('Failed to add course to classroom', 'danger')
    return redirect(url_for('view_classroom', classroom_id=classroom_id))

@app.route('/classrooms/<int:classroom_id>/grades')
@login_required
@admin_required
def grades_classroom(classroom_id):
    classroom = Classroom.get_by_id(classroom_id)
    if not classroom:
        flash('Classroom not found', 'danger')
        return redirect(url_for('classrooms'))
    
    return render_template('grades_classroom.html', classroom=classroom)

@app.route('/classrooms/<int:classroom_id>/grades/<int:student_id>', methods=['GET'])
@login_required
@admin_required
def view_student_grades(classroom_id, student_id):
    classroom = Classroom.get_by_id(classroom_id)
    student = User.get_by_id(student_id)
    if not classroom or not student:
        flash('Classroom or Student not found', 'danger')
        return redirect(url_for('grades_classroom', classroom_id=classroom_id))

    grades = Grade.query.filter_by(student_id=student_id).all()
    grades_dict = {grade.course_id: grade for grade in grades}

    return render_template('student_grades.html', classroom=classroom, student=student, grades_dict=grades_dict)

@app.route('/classrooms/<int:classroom_id>/edit_grade/<int:course_id>/<int:student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_grade(classroom_id, course_id, student_id):
    classroom = Classroom.get_by_id(classroom_id)
    grades = Grade.query.filter_by(student_id=student_id).all()
    grades_dict = {grade.course_id: grade for grade in grades}
    if not classroom:
        flash('Classroom not found', 'danger')
        return redirect(url_for('classrooms'))
    
    course = Course.get_course_by_id(course_id)
    if not course:
        flash('Course not found', 'danger')
        return redirect(url_for('view_classroom', classroom_id=classroom_id))
    
    student = User.query.get(student_id)
    if not student or student.role != 'student' or student.classroom_id != classroom_id:
        flash('Student not found or does not belong to this classroom', 'danger')
        return redirect(url_for('view_classroom', classroom_id=classroom_id))
    
    grade = Grade.query.filter_by(course_id=course_id, student_id=student_id).first()
    if not grade:
        grade = Grade(course_id=course_id, student_id=student_id)

    form = GradeForm(obj=grade)
    if form.validate_on_submit():
        grade.value = form.value.data
        db.session.add(grade)
        db.session.commit()
        flash('Grade updated successfully!', 'success')
        return render_template('student_grades.html', classroom=classroom, student=student, grades_dict=grades_dict)
    
    return render_template('edit_grade.html', form=form, classroom=classroom, course=course, student=student)

# ลบฟังก์ชันนี้ได้เลย
# @app.route('/classrooms/<int:classroom_id>/grades/<int:student_id>', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def grade_student(classroom_id, student_id):
#     classroom = Classroom.get_by_id(classroom_id)
#     student = User.get_by_id(student_id)
#     if not classroom or not student:
#         flash('Classroom or Student not found', 'danger')
#         return redirect(url_for('view_classroom', classroom_id=classroom_id))

#     form = GradeForm()
#     form.student_id.data = student_id

#     if request.method == 'GET':
#         while len(form.grades):
#             form.grades.pop_entry()
#         for course in classroom.courses:
#             grade = Grade.query.filter_by(student_id=student_id, course_id=course.id).first()
#             grade_field_form = GradeFieldForm()
#             grade_field_form.course_id.data = course.id
#             grade_field_form.value.data = grade.value if grade else None
#             form.grades.append_entry(grade_field_form)

#     if form.validate_on_submit():
#         app.logger.info('Form validation successful')
#         for grade_form in form.grades:
#             if grade_form.value.data:
#                 app.logger.info(f'Processing grade for course {grade_form.course_id.data} with value {grade_form.value.data}')
#                 grade = Grade.query.filter_by(student_id=student_id, course_id=grade_form.course_id.data).first()
#                 if grade:
#                     grade.value = float(grade_form.value.data)
#                 else:
#                     Grade.add_grade(value=float(grade_form.value.data), student_id=student_id, course_id=grade_form.course_id.data)
#         db.session.commit()
#         flash('Grades saved successfully!', 'success')
#         return redirect(url_for('view_classroom', classroom_id=classroom_id))
#     else:
#         app.logger.info('Form validation failed')
#         app.logger.info(f'Form errors: {form.errors}')
#         for error in form.errors:
#             app.logger.info(f'Error: {error}')

#     return render_template('grade_student.html', form=form, student=student, classroom=classroom)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
