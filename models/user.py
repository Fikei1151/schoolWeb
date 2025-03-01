from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from flask_login import UserMixin
from models.classroom import ClassroomStudents, Classroom  # นำเข้าตารางห้องเรียน

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.String(13), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10))
    role = db.Column(db.String(10), nullable=False)  # 'admin', 'teacher', 'student'
    email = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)  # เก็บ path รูปโปรไฟล์
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ความสัมพันธ์กับ StudentProfile (เฉพาะนักเรียน)
    student_profile = db.relationship('StudentProfile', back_populates='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def education_level(self):
        """ ตรวจสอบระดับการศึกษาของนักเรียนจากห้องเรียน """
        if self.role != 'student':
            return None  # ไม่ใช่นักเรียน ไม่มีระดับการศึกษา

        classroom_student = ClassroomStudents.query.filter_by(student_id=self.id).first()
        if classroom_student and classroom_student.classroom:
            return classroom_student.classroom.education_level  # ดึงจาก Classroom
        return "ไม่ระบุ"


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # รหัสนักเรียน
    full_name_th = db.Column(db.String(100), nullable=True)  # ✅ แก้ให้ nullable=True
    full_name_en = db.Column(db.String(100), nullable=True)  # ✅ แก้ให้ nullable=True
    birth_date = db.Column(db.Date, nullable=True)  # ✅ แก้ให้ nullable=True
    nationality = db.Column(db.String(50), nullable=True)  # ✅ แก้ให้ nullable=True
    blood_type = db.Column(db.String(5), nullable=True)  
    birth_province = db.Column(db.String(50), nullable=True)  # ✅ แก้ให้ nullable=True
    birth_other = db.Column(db.String(50), nullable=True)  
    parent_status = db.Column(db.String(50), nullable=True)  # ✅ แก้ให้ nullable=True
    disability = db.Column(db.String(50), nullable=True)  
    special_talent = db.Column(db.String(255), nullable=True)  

    # เชื่อมกับ GuardianProfile
    guardian = db.relationship('GuardianProfile', back_populates='student', uselist=False, cascade="all, delete-orphan")

    user = db.relationship('User', back_populates='student_profile')

    @property
    def education_level(self):
        """ ดึงระดับการศึกษาจาก Classroom """
        classroom_student = ClassroomStudents.query.filter_by(student_id=self.user_id).first()
        if classroom_student and classroom_student.classroom:
            return classroom_student.classroom.education_level  # ดึงค่าจากห้องเรียน
        return "ไม่ระบุ"


class GuardianProfile(db.Model):
    __tablename__ = 'guardian_profiles'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(100), nullable=True)  # ✅ แก้ให้ nullable=True
    nationality = db.Column(db.String(50), nullable=True)  # ✅ แก้ให้ nullable=True
    status = db.Column(db.String(50), nullable=True)  # ✅ แก้ให้ nullable=True
    occupation = db.Column(db.String(100), nullable=True)  # ✅ แก้ให้ nullable=True
    position = db.Column(db.String(100), nullable=True)  
    workplace = db.Column(db.String(255), nullable=True)  
    income = db.Column(db.String(50), nullable=True)  
    address_no = db.Column(db.String(20), nullable=True)  # ✅ แก้ให้ nullable=True
    moo = db.Column(db.String(20), nullable=True)  
    soi = db.Column(db.String(50), nullable=True)  
    road = db.Column(db.String(100), nullable=True)  
    sub_district = db.Column(db.String(100), nullable=True)  # ✅ แก้ให้ nullable=True
    district = db.Column(db.String(100), nullable=True)  # ✅ แก้ให้ nullable=True
    province = db.Column(db.String(100), nullable=True)  # ✅ แก้ให้ nullable=True
    postal_code = db.Column(db.String(10), nullable=True)  # ✅ แก้ให้ nullable=True
    phone = db.Column(db.String(20), nullable=True)  # ✅ แก้ให้ nullable=True
    email = db.Column(db.String(100), nullable=True)  

    student = db.relationship('StudentProfile', back_populates='guardian')
