from models.user import db
from models.classroom import classroom_courses

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False, unique=True)
    credit = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    classrooms = db.relationship('Classroom', secondary=classroom_courses, backref=db.backref('courses', lazy='dynamic'))

    @staticmethod
    def add_course(name, code, credit, description):
        new_course = Course(name=name, code=code, credit=credit, description=description)
        db.session.add(new_course)
        db.session.commit()

    @staticmethod
    def get_all_courses():
        return Course.query.all()

    @staticmethod
    def get_course_by_id(course_id):
        return Course.query.get(course_id)

    @staticmethod
    def update_course(course_id, name, code, credit, description):
        course = Course.query.get(course_id)
        if course:
            course.name = name
            course.code = code
            course.credit = credit
            course.description = description
            db.session.commit()
            return course
        return None

    @staticmethod
    def delete_course(course_id):
        course = Course.query.get(course_id)
        if course:
            db.session.delete(course)
            db.session.commit()
            return True
        return False
