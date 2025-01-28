from flask import Blueprint, render_template, session, flash, redirect, url_for
from functools import wraps
from models.user import User

from models.subject import Subject, Grade
student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'student':
            flash("Student only!", 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/student/home')
@student_required
def student_home():
    return render_template('student/student_home.html')

