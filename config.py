import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key-please-change'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///school.db'
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///school.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
