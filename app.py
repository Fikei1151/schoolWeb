from flask import Flask, render_template
from config import Config
from database import db

# Import models (เพื่อสร้างตารางได้ตอน db.create_all())
from models.user import User
from models.classroom import Classroom
from models.subject import Subject, ClassroomSubjects
from models.academic import AcademicSettings

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.teacher_routes import teacher_bp
from routes.student_routes import student_bp
from routes.subject_routes import subject_bp
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # สร้างตารางถ้ายังไม่มี พร้อมสร้าง default admin ถ้าไม่มี
    with app.app_context():
        db.create_all()
        create_default_accounts()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(subject_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

def create_default_accounts():
    # ตรวจสอบว่ามี Admin อยู่แล้วหรือไม่
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

    # สร้างบัญชีนักเรียน 4 คน
    for i in range(1, 5):
        citizen_id = f"111111111111{i+2}"
        if not User.query.filter_by(citizen_id=citizen_id).first():
            student = User(
                citizen_id=citizen_id,
                first_name=f"Student{i}",
                last_name="Default",
                gender='M',
                role='student',
                education_level='primary'
            )
            student.set_password('1')
            db.session.add(student)
            print(f"Default student created: citizen_id={citizen_id} / password=1")

    db.session.commit()
    print("Default accounts created successfully.")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
