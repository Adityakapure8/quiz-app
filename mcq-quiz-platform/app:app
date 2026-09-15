from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime, timezone
import os
import io
import json

# ==================== APP CONFIG ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'dev-secret-key-change-in-prod-9f8a7b6c5d4e3f2a1b0c'
)

# Railway / Heroku style DATABASE_URL fix
db_url = os.environ.get('DATABASE_URL', 'sqlite:///quiz.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to continue.'
login_manager.login_message_category = 'warning'


# ==================== MODELS ====================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    has_attempted = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, nullable=True)
    answers_json = db.Column(db.Text, default='{}')


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


# ==================== INIT DB ====================
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin created: admin / admin123")


# ==================== HELPERS ====================
def admin_required():
    return current_user.is_authenticated and current_user.is_admin


# ==================== PUBLIC ROUTES ====================
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# ==================== ADMIN ROUTES ====================
@app.route('/admin')
@login_required
def admin_dashboard():
    if not admin_required():
        return redirect(url_for('user_dashboard'))
    questions = Question.query.order_by(Question.id.asc()).all()
    users = User.query.filter_by(is_admin=False).order_by(User.id.asc()).all()
    return render_template('admin_dashboard.html', questions=questions, users=users)


@app.route('/admin/add_question', methods=['POST'])
@login_required
def add_question():
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.get_json(force=True)
        required = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Missing field: {field}'}), 400
        correct = data['correct_answer'].upper().strip()
        if correct not in ['A', 'B', 'C', 'D']:
            return jsonify({'error': 'Correct answer must be A, B, C or D'}), 400
        q = Question(
            question_text=data['question_text'].strip(),
            option_a=data['option_a'].strip(),
            option_b=data['option_b'].strip(),
            option_c=data['option_c'].strip(),
            option_d=data['option_d'].strip(),
            correct_answer=correct
        )
        db.session.add(q)
        db.session.commit()
        return jsonify({'success': True, 'id': q.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/admin/delete_question/<int:qid>', methods=['DELETE'])
@login_required
def delete_question(qid):
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 403
    q = Question.query.get(qid)
    if not q:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(q)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.get_json(force=True)
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        if len(password) < 4:
            return jsonify({'error': 'Password must be at least 4 characters'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        user = User(
            username=username,
            password=generate_password_hash(password),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'id': user.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/admin/delete_user/<int:uid>', methods=['DELETE'])
@login_required
def delete_user(uid):
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 403
    u = User.query.get(uid)
    if not u:
        return jsonify({'error': 'Not found'}), 404
    if u.is_admin:
        return jsonify({'error': 'Cannot delete admin'}), 400
    db.session.delete(u)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/admin/reset_user/<int:uid>', methods=['POST'])
@login_required
def reset_user(uid):
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 403
    u = User.query.get(uid)
    if not u:
        return jsonify({'error': 'Not found'}), 404
    u.has_attempted = False
    u.score = 0
    u.total_questions = 0
    u.submitted_at = None
    u.answers_json = '{}'
    db.session.commit()
    return jsonify({'success': True})


@app.route('/admin/download_excel')
@login_required
def download_excel():
    if not admin_required():
        return redirect(url_for('index'))

    wb = Workbook()
    ws = wb.active
    ws.title = "Quiz Results"

    headers = ['Rank', 'Username', 'Score', 'Total Questions',
               'Percentage', 'Status', 'Submitted At']
    ws.append(headers)

    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    users = (User.query
             .filter_by(is_admin=False, has_attempted=True)
             .order_by(User.score.desc(), User.submitted_at.asc())
             .all())

    for rank, u in enumerate(users, 1):
        pct = round((u.score / u.total_questions * 100), 2) if u.total_questions else 0
        submitted = u.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if u.submitted_at else '-'
        ws.append([rank, u.username, u.score, u.total_questions,
                   f"{pct}%", "Completed", submitted])

    for col in ws.columns:
        max_len = max((len(str(cell.value)) if cell.value else 0) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max(15, max_len + 4)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f'quiz_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


# ==================== USER ROUTES ====================
@app.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    return render_template('user_dashboard.html', user=current_user)


@app.route('/quiz')
@login_required
def quiz():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    if current_user.has_attempted:
        return redirect(url_for('result'))
    questions = Question.query.order_by(Question.id.asc()).all()
    if not questions:
        flash('No questions available yet. Please contact admin.', 'warning')
        return redirect(url_for('user_dashboard'))

    questions_data = [
        {
            'id': q.id,
            'question_text': q.question_text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d
        }
        for q in questions
    ]
    return render_template('quiz.html', questions=questions_data)


@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    if current_user.is_admin or current_user.has_attempted:
        return jsonify({'error': 'Not allowed'}), 403
    try:
        data = request.get_json(force=True)
        answers = data.get('answers', {})
        questions = Question.query.all()
        score = 0
        for q in questions:
            user_ans = str(answers.get(str(q.id), '')).upper().strip()
            if user_ans == q.correct_answer:
                score += 1

        current_user.score = score
        current_user.total_questions = len(questions)
        current_user.has_attempted = True
        current_user.submitted_at = datetime.now(timezone.utc)
        current_user.answers_json = json.dumps(answers)
        db.session.commit()

        return jsonify({'success': True, 'redirect': url_for('result')})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/result')
@login_required
def result():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    if not current_user.has_attempted:
        return redirect(url_for('user_dashboard'))

    pct = round((current_user.score / current_user.total_questions * 100), 2) \
        if current_user.total_questions else 0

    leaders = (User.query
               .filter_by(is_admin=False, has_attempted=True)
               .order_by(User.score.desc(), User.submitted_at.asc())
               .all())

    rank = None
    for i, u in enumerate(leaders, 1):
        if u.id == current_user.id:
            rank = i
            break

    return render_template(
        'result.html',
        user=current_user,
        pct=pct,
        rank=rank,
        total=len(leaders)
    )


@app.route('/leaderboard')
@login_required
def leaderboard():
    leaders = (User.query
               .filter_by(is_admin=False, has_attempted=True)
               .order_by(User.score.desc(), User.submitted_at.asc())
               .all())

    data = []
    for i, u in enumerate(leaders, 1):
        pct = round((u.score / u.total_questions * 100), 2) if u.total_questions else 0
        data.append({
            'rank': i,
            'username': u.username,
            'score': u.score,
            'total': u.total_questions,
            'pct': pct
        })

    return render_template('leaderboard.html', leaders=data)


@app.route('/api/check_status')
@login_required
def check_status():
    return jsonify({'has_attempted': current_user.has_attempted})


# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('index'))


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return "Server error occurred. Please try again.", 500


# ==================== MAIN ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
