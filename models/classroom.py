from models.user import db

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    academic_year = db.Column(db.String(4), index=True)
    students = db.relationship('User', backref='classroom', lazy='dynamic')

    def __repr__(self):
        return f'<Classroom {self.name}>'

    @staticmethod
    def get_all_classrooms():
        return Classroom.query.all()

    @staticmethod
    def get_by_id(classroom_id):
        return Classroom.query.get(classroom_id)

    @staticmethod
    def add_classroom(name, academic_year):
        classroom = Classroom(name=name, academic_year=academic_year)
        db.session.add(classroom)
        db.session.commit()
        return classroom

    @staticmethod
    def delete_classroom(classroom_id):
        classroom = Classroom.query.get(classroom_id)
        if classroom:
            db.session.delete(classroom)
            db.session.commit()
            return True
        return False

    @staticmethod
    def update_classroom(classroom_id, name, academic_year):
        classroom = Classroom.query.get(classroom_id)
        if classroom:
            classroom.name = name
            classroom.academic_year = academic_year
            db.session.commit()
            return classroom
        return None
