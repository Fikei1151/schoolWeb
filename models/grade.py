from models.user import db

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    course = db.relationship('Course', backref=db.backref('grades', lazy=True))

    @staticmethod
    def add_grade(value, student_id, course_id):
        new_grade = Grade(value=value, student_id=student_id, course_id=course_id)
        db.session.add(new_grade)
        db.session.commit()

    @staticmethod
    def get_grades_by_student(student_id):
        return Grade.query.filter_by(student_id=student_id).all()

    @staticmethod
    def get_grades_by_course(course_id):
        return Grade.query.filter_by(course_id=course_id).all()

    @staticmethod
    def update_grade(grade_id, value):
        grade = Grade.query.get(grade_id)
        if grade:
            grade.value = value
            db.session.commit()
            return grade
        return None

    @staticmethod
    def delete_grade(grade_id):
        grade = Grade.query.get(grade_id)
        if grade:
            db.session.delete(grade)
            db.session.commit()
            return True
        return False
