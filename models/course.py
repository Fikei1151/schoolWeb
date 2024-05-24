from models.user import db

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    credit = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    classrooms = db.relationship('Classroom', secondary='classroom_courses', back_populates='courses')

    @staticmethod
    def add_course(name, code, credit, description=None):
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
    def get_by_id(course_id):  # เปลี่ยนชื่อฟังก์ชันให้ตรงกับการใช้งาน
        return Course.query.get(course_id)

    @staticmethod
    def update_course(course_id, name, code, credit, description=None):
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
