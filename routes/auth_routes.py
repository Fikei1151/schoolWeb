from flask import Blueprint, request, redirect, url_for, flash, render_template, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from database import db
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        citizen_id = request.form.get('citizen_id')
        password = request.form.get('password')
        user = User.query.filter_by(citizen_id=citizen_id).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)  # ✅ บันทึกสถานะ Login
            session['user_id'] = user.id  # ✅ เก็บ User ID ใน Session
            session['role'] = user.role  # ✅ เก็บ Role ใน Session
            session.modified = True  # ✅ บังคับให้ Flask อัปเดต Session
            flash('เข้าสู่ระบบสำเร็จ!', 'success')
            return redirect(url_for('index'))
        else:
            flash('รหัสประชาชนหรือรหัสผ่านไม่ถูกต้อง', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    print(f"DEBUG: Logging out user -> {current_user.get_id()}, Role: {current_user.role}")  # ✅ Debugging
    logout_user()  # ✅ ออกจากระบบ Flask-Login
    session.clear()  # ✅ ล้าง session ทั้งหมด
    session.modified = True  # ✅ บังคับให้ Flask อัปเดต session จริงๆ

    # ✅ ล้าง Cookie ของ Remember Me
    response = redirect(url_for('auth.login'))
    response.delete_cookie('remember_token')

    flash("ออกจากระบบสำเร็จ", "success")
    return response
