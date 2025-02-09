from database import db

class Classroom(db.Model):
    __tablename__ = 'classroom'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    education_level = db.Column(db.String(50), nullable=False)  # จะเก็บเป็น "ประถมศึกษา" หรือ "มัธยมศึกษา"
    grade_level = db.Column(db.Integer, nullable=False)  # เช่น 1, 2, 3, ...
    creation_year = db.Column(db.Integer, nullable=False)  # เปลี่ยนชื่อจาก academic_year เป็น creation_year
    semester = db.Column(db.Integer, nullable=False)  # เทอม เช่น 1 หรือ 2
    room_number = db.Column(db.Integer, nullable=False)  # ห้องที่เท่าไหร่ (ใช้สร้างชื่อห้องอัตโนมัติ)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    teacher = db.relationship('User', backref='classrooms')
    subjects = db.relationship('ClassroomSubjects', back_populates='classroom')

class ClassroomStudents(db.Model):
    __tablename__ = 'classroom_students'
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)  # แก้เป็น classroom.id
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    classroom = db.relationship("Classroom", backref="students")
    student = db.relationship("User", backref="enrolled_classrooms")