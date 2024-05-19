from models.user import db

# ตารางความสัมพันธ์ many-to-many ระหว่าง Classroom และ Course
classroom_courses = db.Table('classroom_courses',
    db.Column('classroom_id', db.Integer, db.ForeignKey('classroom.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    academic_year = db.Column(db.String(64), nullable=False)
    students = db.relationship('User', backref='classroom', lazy='dynamic')

    @staticmethod
    def get_all_classrooms():
        return Classroom.query.all()

    @staticmethod
    def get_by_id(classroom_id):
        return Classroom.query.get(classroom_id)

    @staticmethod
    def add_classroom(name, academic_year):
        new_classroom = Classroom(name=name, academic_year=academic_year)
        db.session.add(new_classroom)
        db.session.commit()

    @staticmethod
    def update_classroom(classroom_id, name, academic_year):
        classroom = Classroom.query.get(classroom_id)
        if classroom:
            classroom.name = name
            classroom.academic_year = academic_year
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
