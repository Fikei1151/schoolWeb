from models.user import db

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    grade = db.Column(db.String(2), nullable=False)

    student = db.relationship('User', backref='grades')
    course = db.relationship('Course', backref='grades')

    def __repr__(self):
        return f'<Grade {self.grade} for {self.student.username} in {self.course.name}>'

    @staticmethod
    def get_grades_by_student(student_id):
        return Grade.query.filter_by(student_id=student_id).all()

    @staticmethod
    def get_grades_by_course(course_id):
        return Grade.query.filter_by(course_id=course_id).all()

    @staticmethod
    def add_grade(student_id, course_id, grade):
        new_grade = Grade(student_id=student_id, course_id=course_id, grade=grade)
        db.session.add(new_grade)
        db.session.commit()

    @staticmethod
    def update_grade(grade_id, grade):
        grade = Grade.query.get(grade_id)
        if grade:
            grade.grade = grade
            db.session.commit()

    @staticmethod
    def delete_grade(grade_id):
        grade = Grade.query.get(grade_id)
        if grade:
            db.session.delete(grade)
            db.session.commit()
