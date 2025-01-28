from datetime import datetime
from database import db

class AcademicSettings(db.Model):
    __tablename__ = 'academic_settings'
    id = db.Column(db.Integer, primary_key=True)
    current_year = db.Column(db.Integer, nullable=False)    # เช่น 2568
    current_semester = db.Column(db.Integer, nullable=False) # 1, 2
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
