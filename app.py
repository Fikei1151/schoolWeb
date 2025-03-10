from flask import Flask, render_template, session
from config import Config
from database import db
import os
from datetime import datetime
from utils.s3_utils import s3_client, upload_file_to_s3
from models.user import User, StudentProfile, GuardianProfile
from models.classroom import Classroom, ClassroomStudents
from models.subject import Subject, ClassroomSubjects, Grade, subject_teachers
from models.academic import AcademicSettings
from models.registration import AdmissionPeriod, ExamRoom, StudentApplication
from models.post import Post  # เพิ่ม Post model
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.teacher_routes import teacher_bp
from routes.student_routes import student_bp
from routes.subject_routes import subject_bp
from routes.news_routes import news_bp
from routes.user_routes import user_bp
from routes.registration_routes import registration_bp
from flask_session import Session
from flask_login import LoginManager, current_user
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Session(app)

    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    local_upload_folder = os.path.join(os.getcwd(), 'static', 'uploads')
    if not os.path.exists(local_upload_folder):
        os.makedirs(local_upload_folder)

    # Initialize database and migration
    db.init_app(app)
    migrate = Migrate(app, db)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.before_request
    def clear_stale_user():
        if not current_user.is_authenticated:
            session.clear()
            session.modified = True

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(subject_bp)
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(user_bp)
    app.register_blueprint(registration_bp, url_prefix='/registration')

    @app.route('/')
    def index():
        return render_template('index.html')

    # ตรวจสอบและสร้างตารางถ้ายังไม่มี
    with app.app_context():
        try:
            # ตรวจสอบตารางที่มีอยู่ใน database
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()

            # ดึงตารางจาก models อัตโนมัติ (ที่ inherit จาก db.Model)
            expected_tables = [model.__tablename__ for model in db.Model.__subclasses__()]

            # เพิ่มตารางที่กำหนดแบบ manual (เช่น db.Table)
            manual_tables = [
                'subject_teachers',  # จาก subject_teachers (ตารางกลาง)
                'classroom_students'  # จาก ClassroomStudents (ตารางกลาง)
            ]
            expected_tables.extend(manual_tables)

            # ตรวจสอบว่ามีตารางครบหรือไม่
            missing_tables = [table for table in expected_tables if table not in existing_tables]

            if missing_tables:
                print(f"Missing tables: {missing_tables}. Creating tables...")
                # สร้างตารางที่ไม่มี
                db.create_all()
                print("Tables created successfully!")
            else:
                print("All tables already exist. No need to create.")

            # (ถ้ามี Flask-Migrate) รัน migration เพื่อให้แน่ใจว่าตาราง sync กับ models
            # ถ้าคุณใช้ Flask-Migrate และมีการเปลี่ยนแปลงใน models
            # คุณควรรัน migration ด้วยคำสั่ง:
            # flask db migrate -m "Initial migration"
            # flask db upgrade

        except Exception as e:
            print(f"Error checking or creating tables: {str(e)}")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)