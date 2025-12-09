from flask import Blueprint, render_template, url_for, flash, redirect, request, session
from flask_login import login_required, current_user
from schoolapp import db
from schoolapp.models import Review

review_bp = Blueprint('review', __name__)

@review_bp.route("/review", methods=['GET', 'POST'])
def review():
    username = current_user.username if current_user.is_authenticated else session.get('username')
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('請先登入再留言！', 'danger')
            return redirect(url_for('auth.login'))
        try:
            rating = int(request.form.get('rating', 0))
        except ValueError:
            flash('評分格式錯誤。', 'danger')
            return redirect(url_for('review.review'))
        comment = request.form.get('comment', '').strip()
        if not comment:
            flash('留言內容不可為空。', 'warning')
            return redirect(url_for('review.review'))
        new_review = Review(comment=comment, rating=rating, user_id=current_user.id)
        db.session.add(new_review)
        db.session.commit()
        flash('感謝您的評價！', 'success')
        return redirect(url_for('review.review'))

    reviews_q = Review.query.order_by(Review.date_posted.desc()).all()
    reviews = []
    for r in reviews_q:
        uname = r.author.username if r.author else '匿名'
        reviews.append({
            'username': uname,
            'rating': r.rating,
            'comment': r.comment,
            'date_posted': r.date_posted
        })
    return render_template('review.html', reviews=reviews, user=username)