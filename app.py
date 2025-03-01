from flask import Flask, render_template,session
from config import Config
from database import db
import os
from datetime import datetime 
# Import models (เพื่อสร้างตารางได้ตอน db.create_all())
from models.user import User, StudentProfile
from models.classroom import Classroom
from models.subject import Subject, ClassroomSubjects
from models.academic import AcademicSettings

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.teacher_routes import teacher_bp
from routes.student_routes import student_bp
from routes.subject_routes import subject_bp
from routes.news_routes import news_bp
from routes.user_routes import user_bp 
from flask_session import Session  
# Import Flask-Login
from flask_login import LoginManager,current_user

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Session(app)    
    # ตั้งค่าโฟลเดอร์สำหรับอัปโหลดไฟล์
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

    # เริ่มต้น SQLAlchemy
    db.init_app(app)

    # ตั้งค่า Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # เมื่อผู้ใช้ยังไม่ได้เข้าสู่ระบบจะถูกเปลี่ยนเส้นทางไปยังหน้า login

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # สร้างตารางถ้ายังไม่มี พร้อมสร้าง default account
    @app.before_request
    def clear_stale_user():
        if not current_user.is_authenticated:
            session.clear()
            session.modified = True  # ✅ บังคับ Flask อัปเดต Session
    with app.app_context():
        db.create_all()
        create_default_accounts()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(subject_bp)
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(user_bp)

    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

def create_default_accounts():
    """สร้างบัญชีเริ่มต้น (Admin, Teacher, Student)"""
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        new_admin = User(
            citizen_id='1234567890123',
            first_name='Default',
            last_name='Admin',
            gender='M',
            role='admin'
        )
        new_admin.set_password('admin1234')
        db.session.add(new_admin)
        print("Default admin created: citizen_id=1234567890123 / password=admin1234")

    # สร้างบัญชีครู 2 คน
    for i in range(1, 3):
        citizen_id = f"111111111111{i}"
        if not User.query.filter_by(citizen_id=citizen_id).first():
            teacher = User(
                citizen_id=citizen_id,
                first_name=f"Teacher{i}",
                last_name="Default",
                gender='M',
                role='teacher'
            )
            teacher.set_password('1')
            db.session.add(teacher)
            print(f"Default teacher created: citizen_id={citizen_id} / password=1")

    # สร้างบัญชีนักเรียน 4 คน พร้อม StudentProfile
    for i in range(1, 5):
        citizen_id = f"111111111111{i+2}"
        if not User.query.filter_by(citizen_id=citizen_id).first():
            student = User(
                citizen_id=citizen_id,
                first_name=f"Student{i}",
                last_name="Default",
                gender='M',
                role='student'
            )
            student.set_password('1')
            db.session.add(student)

            # สร้าง StudentProfile โดยไม่กำหนด education_level (ระบบจะดึงจากห้องเรียน)
            student_profile = StudentProfile(
                user=student,
                student_id=f"S{i+100}",
                full_name_th=f"นักเรียน {i}",
                full_name_en=f"Student {i}",
                birth_date=datetime(2010, 1, 1),
                nationality="ไทย",
                parent_status="มีชีวิต",
                disability="ไม่มี"
            )
            db.session.add(student_profile)

            print(f"Default student created: citizen_id={citizen_id} / password=1")

    db.session.commit()
    print("Default accounts created successfully.")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True,port=8000)
