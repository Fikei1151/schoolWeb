from models.user import db, User

classroom_courses = db.Table('classroom_courses',
    db.Column('classroom_id', db.Integer, db.ForeignKey('classroom.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
    extend_existing=True
)


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
    teacher = db.relationship('User', back_populates='teacher_classroom', foreign_keys=[teacher_id])
    students = db.relationship('User', back_populates='classroom', foreign_keys=[User.classroom_id])
    courses = db.relationship('Course', secondary='classroom_courses', back_populates='classrooms')  # เพิ่ม back_populates

    @staticmethod
    def add_classroom(name, academic_year, teacher_id=None):
        new_classroom = Classroom(name=name, academic_year=academic_year, teacher_id=teacher_id)
        db.session.add(new_classroom)
        db.session.commit()

    @staticmethod
    def get_all_classrooms():
        return Classroom.query.all()

    @staticmethod
    def get_by_id(classroom_id):
        return Classroom.query.get(classroom_id)

    @staticmethod
    def update_classroom(classroom_id, name, academic_year, teacher_id=None):
        classroom = Classroom.query.get(classroom_id)
        if classroom:
            classroom.name = name
            classroom.academic_year = academic_year
            classroom.teacher_id = teacher_id
            db.session.commit()
            return classroom
        return None

    @staticmethod
    def delete_classroom(classroom_id):
        classroom = Classroom.query.get(classroom_id)
        if classroom:
            db.session.delete(classroom)
            db.session.commit()
            return True
        return False
