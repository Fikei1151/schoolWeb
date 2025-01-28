from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from database import db
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        citizen_id = request.form.get('citizen_id')
        password = request.form.get('password')
        user = User.query.filter_by(citizen_id=citizen_id).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash("Login successful", 'success')
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials", 'error')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
