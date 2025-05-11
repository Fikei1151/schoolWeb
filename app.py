from flask import Flask, render_template, session, url_for, send_from_directory
from config import Config
from database import db
import os
from datetime import datetime
from utils.s3_utils import storage, upload_file_to_storage, get_file_url
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

    # ตั้งค่าโฟลเดอร์สำหรับอัปโหลด
    # สร้างโฟลเดอร์ในเซิร์ฟเวอร์ถ้ายังไม่มี
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    
    # สร้างโฟลเดอร์ย่อยสำหรับประเภทไฟล์ต่างๆ
    os.makedirs(os.path.join(upload_folder, 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'profile_pics'), exist_ok=True)
    
    # สร้างโฟลเดอร์ static/uploads สำหรับเก็บไฟล์ชั่วคราวหากจำเป็น
    local_upload_folder = os.path.join(os.getcwd(), 'static', 'uploads')
    if not os.path.exists(local_upload_folder):
        os.makedirs(local_upload_folder, exist_ok=True)

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

    # Initialize database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
            
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"Available tables: {', '.join(existing_tables)}")
            
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")

    # File access routes
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'uploads'), filename)
    
    @app.route('/profile_pics/<path:filename>')
    def profile_image(filename):
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics'), filename)

    # File URL helper
    @app.context_processor
    def utility_processor():
        def get_upload_url(path):
            if not path:
                return None
            if path.startswith(('http://', 'https://')):
                return path
            return get_file_url(path)
        return dict(get_upload_url=get_upload_url)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)