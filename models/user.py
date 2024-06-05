from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'))
    classroom = db.relationship('Classroom', back_populates='students', foreign_keys=[classroom_id])
    grades = db.relationship('Grade', backref='student', lazy=True)
    teacher_classroom = db.relationship('Classroom', back_populates='teacher', uselist=False, foreign_keys='Classroom.teacher_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_user_id(user_id):
        return User.query.filter_by(user_id=user_id).first()

    @staticmethod
    def get_all_students():
        return User.query.filter_by(role='student').all()

    @staticmethod
    def get_by_id(user_id):
        return User.query.get(user_id)
