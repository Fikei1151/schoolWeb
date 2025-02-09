from database import db

# ตารางกลาง subject_teachers เพื่อเก็บว่าครู (teacher_id) คนไหน สอนวิชา (subject_id) อะไร
subject_teachers = db.Table(
    'subject_teachers',
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class Subject(db.Model):
    __tablename__ = 'subject'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # ฟิลด์ใหม่: ใครเป็นคนสร้าง (owner) - อาจเป็นครูหรือแอดมิน
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # ผู้สอน (อาจมีหลายคน) -> หลายต่อหลาย
    teachers = db.relationship(
        "User", 
        secondary=subject_teachers, 
        backref="taught_subjects"
    )

    # ความสัมพันธ์ไปหา user ที่เป็น owner ของ subject
    owner = db.relationship("User", foreign_keys=[created_by], backref="owned_subjects")

    classrooms = db.relationship('ClassroomSubjects', back_populates='subject')

class ClassroomSubjects(db.Model):
    __tablename__ = 'classroom_subjects'

    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # ✅ เพิ่ม ForeignKey ไปยังตาราง users

    classroom = db.relationship('Classroom', back_populates='subjects')
    subject = db.relationship('Subject', back_populates='classrooms')
    teacher = db.relationship('User', backref='teaching_subjects')  # ✅ ตอนนี้ใช้งานได้ถูกต้อง

class Grade(db.Model):
    __tablename__ = 'grades'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    grade = db.Column(db.Float, nullable=True)

    term = db.Column(db.String(10), nullable=False)  # เช่น '1/2565'
    grade_level = db.Column(db.Integer, nullable=False)  # แก้จาก String เป็น Integer
    education_level = db.Column(db.String(50), nullable=False)  # "primary" หรือ "secondary"
    academic_year = db.Column(db.Integer, nullable=False)  # ปีการศึกษา เช่น 2568
    semester = db.Column(db.Integer, nullable=False)  # เทอม เช่น 1 หรือ 2

    student = db.relationship("User", backref="grades")
    subject = db.relationship("Subject", backref="grades")

    def get_grade_display(self):
        """แปลงเลข grade_level เป็นข้อความที่เข้าใจง่าย"""
        if self.grade_level <= 6:
            return f"ป.{self.grade_level}"
        return f"ม.{self.grade_level - 6}"
