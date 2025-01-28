from database import db

class Classroom(db.Model):
    __tablename__ = 'classroom'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    education_level = db.Column(db.String(50), nullable=False)  # primary, secondary
    grade_level = db.Column(db.Integer, nullable=False)  # เช่น 1, 2, 3
    academic_year = db.Column(db.Integer, nullable=False)  # ปีการศึกษา เช่น 2568
    semester = db.Column(db.Integer, nullable=False)  # เทอม เช่น 1 หรือ 2
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