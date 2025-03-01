import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from PIL import Image
from database import db
from models.post import Post
from functools import wraps

from io import BytesIO

news_bp = Blueprint('news', __name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('กรุณาเข้าสู่ระบบก่อน', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """ ตรวจสอบว่าสามารถอัปโหลดไฟล์นี้ได้หรือไม่ """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_image(image_path):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        
        # ✅ ปรับขนาดให้ไม่เกิน 1080px ด้านยาวสุด
        max_size = (1080, 1080)
        img.thumbnail(max_size, Image.ANTIALIAS)
        
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=75)  # ✅ ลดคุณภาพลงเล็กน้อย
        with open(image_path, "wb") as f:
            f.write(buffer.getvalue())
    except Exception as e:
        print(f"Error compressing image: {e}")


@news_bp.route('/news-feed')
def news_feed():
    posts = Post.query.filter_by(is_approved=True).order_by(Post.date.desc()).all()
    return render_template('news/news_feed.html', posts=posts)


# ✅ หน้าโพสต์ข่าว (รองรับบีบอัดภาพ)
@news_bp.route('/post-news', methods=['GET', 'POST'])
@login_required
def post_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_file = request.files.get('image')
        file_file = request.files.get('file')
        author_id = session.get('user_id')

        image_path, file_path = None, None

        # ✅ บันทึกไฟล์รูปภาพ
        if image_file:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('static/uploads', filename)
            image_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

            # ✅ บีบอัดภาพก่อนบันทึก
            compress_image(image_path)

        # ✅ บันทึกไฟล์เอกสาร
        if file_file:
            filename = secure_filename(file_file.filename)
            file_path = os.path.join('static/uploads', filename)
            file_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

        new_post = Post(
            title=title,
            content=content,
            author_id=author_id,
            image_path=image_path.replace('static/', '') if image_path else None,
            file_path=file_path.replace('static/', '') if file_path else None,
            is_approved=False
        )

        db.session.add(new_post)
        db.session.commit()
        flash('โพสต์ของคุณถูกส่งไปให้แอดมินอนุมัติ', 'success')
        return redirect(url_for('news.news_feed'))

    return render_template('news/post_news.html')


@news_bp.route('/edit-news/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_news(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author_id != session.get('user_id') and session.get('role') != 'admin':
        flash('คุณไม่มีสิทธิ์แก้ไขโพสต์นี้', 'danger')
        return redirect(url_for('news.news_feed'))

    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')

        db.session.commit()
        flash('โพสต์ถูกแก้ไขเรียบร้อย', 'success')
        return redirect(url_for('news.news_feed'))

    return render_template('news/edit_news.html', post=post)


@news_bp.route('/delete-news/<int:post_id>', methods=['POST'])
@login_required
def delete_news(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author_id != session.get('user_id') and session.get('role') != 'admin':
        flash('คุณไม่มีสิทธิ์ลบโพสต์นี้', 'danger')
        return redirect(url_for('news.news_feed'))

    # ✅ ลบไฟล์จากเซิร์ฟเวอร์
    if post.image_path:
        image_path = os.path.join('static', post.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    if post.file_path:
        file_path = os.path.join('static', post.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(post)
    db.session.commit()
    flash('โพสต์ถูกลบเรียบร้อยแล้ว!', 'success')
    return redirect(url_for('news.news_feed'))



@news_bp.route('/admin/approve-news')
@login_required
def approve_news():
    if session.get('role') != 'admin':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('news.news_feed'))

    pending_posts = Post.query.filter_by(is_approved=False).all()
    return render_template('news/admin_approve_news.html', posts=pending_posts)


@news_bp.route('/admin/approve-news/<int:post_id>/approve')
@login_required
def approve_post(post_id):
    if session.get('role') != 'admin':
        flash('คุณไม่มีสิทธิ์ทำรายการนี้', 'danger')
        return redirect(url_for('news.news_feed'))

    post = Post.query.get_or_404(post_id)
    post.is_approved = True
    db.session.commit()
    flash('โพสต์ได้รับการอนุมัติแล้ว!', 'success')
    return redirect(url_for('news.approve_news'))
