from datetime import datetime
from database import db

class AdmissionPeriod(db.Model):
    """ตารางเก็บข้อมูลช่วงเวลารับสมัครนักเรียน"""
    __tablename__ = 'admission_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    academic_year = db.Column(db.Integer, nullable=False)  # ปีการศึกษา เช่น 2568
    education_level = db.Column(db.String(50), nullable=False)  # "ประถมศึกษา" หรือ "มัธยมศึกษา"
    grade_level = db.Column(db.Integer, nullable=False)  # ระดับชั้น เช่น 1, 2, 3
    start_date = db.Column(db.Date, nullable=False)  # วันที่เริ่มรับสมัคร
    end_date = db.Column(db.Date, nullable=False)  # วันที่ปิดรับสมัคร
    is_active = db.Column(db.Boolean, default=True)  # สถานะการเปิด/ปิดรับสมัคร
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ความสัมพันธ์กับ StudentApplication
    applications = db.relationship('StudentApplication', back_populates='admission_period')
    
    def is_open(self):
        """ตรวจสอบว่าช่วงรับสมัครนี้เปิดอยู่หรือไม่"""
        today = datetime.utcnow().date()
        return (self.is_active and 
                self.start_date <= today <= self.end_date)
    
    def __repr__(self):
        return f"<AdmissionPeriod {self.academic_year} {self.education_level} ชั้น {self.grade_level}>"


class ExamRoom(db.Model):
    """ตารางเก็บข้อมูลห้องสอบ"""
    __tablename__ = 'exam_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # ชื่อห้องสอบ เช่น "ห้องสอบ 1"
    capacity = db.Column(db.Integer, nullable=False)  # จำนวนที่นั่งสูงสุด
    exam_date = db.Column(db.Date, nullable=False)  # วันที่สอบ
    exam_time = db.Column(db.String(50), nullable=False)  # เวลาสอบ เช่น "09:00-12:00"
    location = db.Column(db.String(255), nullable=False)  # สถานที่ห้องสอบ
    education_level = db.Column(db.String(50), nullable=False)  # "ประถมศึกษา" หรือ "มัธยมศึกษา"
    grade_level = db.Column(db.Integer, nullable=False)  # ระดับชั้น เช่น 1, 2, 3
    academic_year = db.Column(db.Integer, nullable=False)  # ปีการศึกษา
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ความสัมพันธ์กับ StudentApplication
    applications = db.relationship('StudentApplication', back_populates='exam_room')
    
    def get_current_applicants_count(self):
        """นับจำนวนผู้สมัครปัจจุบันในห้องสอบนี้"""
        return StudentApplication.query.filter_by(exam_room_id=self.id).count()
    
    def is_full(self):
        """ตรวจสอบว่าห้องสอบเต็มหรือไม่"""
        return self.get_current_applicants_count() >= self.capacity
    
    def __repr__(self):
        return f"<ExamRoom {self.name} - {self.exam_date}>"


class StudentApplication(db.Model):
    """ตารางเก็บข้อมูลการสมัครเรียน"""
    __tablename__ = 'student_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    admission_period_id = db.Column(db.Integer, db.ForeignKey('admission_periods.id'), nullable=False)
    exam_room_id = db.Column(db.Integer, db.ForeignKey('exam_rooms.id'), nullable=True)  # อาจจะยังไม่ได้กำหนดห้องสอบตอนสมัคร
    
    application_number = db.Column(db.String(20), unique=True, nullable=False)  # เลขที่ใบสมัคร
    application_date = db.Column(db.DateTime, default=datetime.utcnow)  # วันที่สมัคร
    status = db.Column(db.String(20), default='pending')  # สถานะ: pending, approved, rejected
    is_converted_to_student = db.Column(db.Boolean, default=False)  # สถานะการแปลงเป็นบัญชีนักเรียน
    
    # ข้อมูลนักเรียน
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    citizen_id = db.Column(db.String(13), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    blood_type = db.Column(db.String(5), nullable=True)
    birth_province = db.Column(db.String(50), nullable=True)
    birth_other = db.Column(db.String(50), nullable=True)
    disability = db.Column(db.String(50), nullable=True)
    special_talent = db.Column(db.String(255), nullable=True)
    
    # ข้อมูลผู้ปกครอง
    guardian_full_name = db.Column(db.String(100), nullable=False)
    guardian_nationality = db.Column(db.String(50), nullable=False)
    guardian_status = db.Column(db.String(50), nullable=False)  # ความสัมพันธ์กับนักเรียน
    guardian_occupation = db.Column(db.String(100), nullable=False)
    guardian_position = db.Column(db.String(100), nullable=True)
    guardian_workplace = db.Column(db.String(255), nullable=True)
    guardian_income = db.Column(db.String(50), nullable=True)
    guardian_address_no = db.Column(db.String(20), nullable=False)
    guardian_moo = db.Column(db.String(20), nullable=True)
    guardian_soi = db.Column(db.String(50), nullable=True)
    guardian_road = db.Column(db.String(100), nullable=True)
    guardian_sub_district = db.Column(db.String(100), nullable=False)
    guardian_district = db.Column(db.String(100), nullable=False)
    guardian_province = db.Column(db.String(100), nullable=False)
    guardian_postal_code = db.Column(db.String(10), nullable=False)
    guardian_phone = db.Column(db.String(20), nullable=False)
    guardian_email = db.Column(db.String(100), nullable=True)
    
    # ความสัมพันธ์
    admission_period = db.relationship('AdmissionPeriod', back_populates='applications')
    exam_room = db.relationship('ExamRoom', back_populates='applications')
    
    def __repr__(self):
        return f"<StudentApplication {self.application_number} - {self.first_name} {self.last_name}>"
    
    @classmethod
    def generate_application_number(cls, academic_year, education_level, grade_level):
        """สร้างเลขที่ใบสมัครอัตโนมัติ"""
        # รูปแบบ: ปีการศึกษา-ระดับ-ชั้น-ลำดับ
        # เช่น 2568-P-1-0001 (ประถมศึกษาปีที่ 1)
        # หรือ 2568-M-1-0001 (มัธยมศึกษาปีที่ 1)
        
        # กำหนดรหัสระดับการศึกษา
        level_code = 'P' if education_level == 'ประถมศึกษา' else 'M'
        
        # หาลำดับล่าสุดในปีการศึกษา ระดับ และชั้นนี้
        prefix = f"{academic_year}-{level_code}-{grade_level}-"
        latest_app = cls.query.filter(
            cls.application_number.like(f"{prefix}%")
        ).order_by(cls.application_number.desc()).first()
        
        if latest_app:
            # ดึงลำดับล่าสุดและเพิ่มอีก 1
            last_sequence = int(latest_app.application_number.split('-')[-1])
            new_sequence = last_sequence + 1
        else:
            # ถ้าไม่มีใบสมัครก่อนหน้า เริ่มที่ 1
            new_sequence = 1
        
        # สร้างเลขที่ใบสมัครใหม่
        return f"{prefix}{new_sequence:04d}"
