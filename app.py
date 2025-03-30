from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy.orm import scoped_session, sessionmaker
from models.db_setup import engine, User, Subject, Chapter  # ✅ Import Subject model
from werkzeug.security import check_password_hash
from functools import wraps  # For login-required decorator
from datetime import datetime

app = Flask(__name__)
app.secret_key = "0802005"  # Change this to a strong key

# Create a database session factory
Session = scoped_session(sessionmaker(bind=engine))

# === Login Required Decorator ===
def login_required(role=None):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Access denied!", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# === INDEX / HOME ===
@app.route('/')
def index():
    if "user_id" in session:
        return redirect(url_for("admin_dashboard" if session["role"] == "admin" else "user_dashboard"))
    return render_template('index.html')

# === AUTHENTICATION ROUTES ===
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        session_db = Session()
        user = session_db.query(User).filter_by(email=email).first()
        session_db.close()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["role"] = user.role
            flash("Login successful!", "success")

            return redirect(url_for("admin_dashboard" if user.role == "admin" else "user_dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        qualification = request.form.get("qualification", "")
        dob = request.form["dob"]

        # Ensure dob is parsed correctly
        try:
            dob = datetime.strptime(dob, "%Y-%m-%d").date() if dob else None
        except ValueError:
            flash("Invalid date format for Date of Birth. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for("register"))

        session_db = Session()
        existing_user = session_db.query(User).filter_by(email=email).first()

        if existing_user:
            session_db.close()
            flash("Email already registered. Please log in.", "danger")
            return redirect(url_for("register"))

        # Create and add new user
        new_user = User(email=email, full_name=full_name, qualification=qualification, dob=dob, role="user")
        new_user.set_password(password)
        session_db.add(new_user)
        session_db.commit()
        session_db.close()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# === USER ROUTES (Protected) ===
@app.route('/user/dashboard')
@login_required(role="user")
def user_dashboard():
    return render_template('user/user_dashboard.html')

@app.route('/user/summary')
@login_required(role="user")
def user_summary():
    return render_template('user/user_summary.html')

@app.route('/user/scores')
@login_required(role="user")
def user_scores():
    return render_template('user/scores.html')

@app.route('/user/quiz/<int:quiz_id>')
@login_required(role="user")
def view_quiz(quiz_id):
    return render_template('user/view_quiz.html', quiz_id=quiz_id)

@app.route('/user/take-quiz/<int:quiz_id>')
@login_required(role="user")
def take_quiz(quiz_id):
    return render_template('user/take_quiz.html', quiz_id=quiz_id)

# === ADMIN ROUTES (Protected) ===
@app.route('/admin/dashboard')
@login_required(role="admin")
def admin_dashboard():
    return render_template('admin/adm_dashboard.html')

@app.route('/admin/summary')
@login_required(role="admin")
def admin_summary():
    return render_template('admin/adm_summary.html')

@app.route('/admin/manage-quizzes')
@login_required(role="admin")
def quiz_management():
    return render_template('admin/quiz_management.html')

# === SUBJECT CRUD ===
@app.route("/admin/subjects")
@login_required(role="admin")
def subject_management():
    session_db = Session()
    subjects = session_db.query(Subject).all()
    session_db.close()

    return render_template("admin/subject_management.html", subjects=subjects)

# ✅ FIXED: Added route for adding a subject
@app.route('/admin/new-subject', methods=['GET', 'POST'])
@login_required(role="admin")
def new_subject():
    if request.method == 'POST':
        if "name" not in request.form:
            flash("Subject name is required!", "danger")
            return redirect(url_for('new_subject'))

        name = request.form.get("name").strip()

        if not name:
            flash("Subject name cannot be empty!", "danger")
            return redirect(url_for('new_subject'))

        session_db = Session()
        new_subject = Subject(name=name)
        session_db.add(new_subject)
        session_db.commit()
        session_db.close()

        flash("Subject added successfully!", "success")
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard

    return render_template('admin/new_subject.html')

@app.route("/admin/subjects/edit/<int:subject_id>", methods=["POST"])
@login_required(role="admin")
def edit_subject(subject_id):
    session_db = Session()
    subject = session_db.query(Subject).get(subject_id)

    if subject:
        subject.name = request.form["name"]
        subject.description = request.form["description"]
        session_db.commit()
        flash("Subject updated successfully!", "success")
    else:
        flash("Subject not found!", "danger")

    session_db.close()
    return redirect(url_for("subject_management"))

@app.route("/admin/subjects/delete/<int:subject_id>", methods=["POST"])
@login_required(role="admin")
def delete_subject(subject_id):
    session_db = Session()
    subject = session_db.query(Subject).get(subject_id)

    if subject:
        session_db.delete(subject)
        session_db.commit()
        flash("Subject deleted successfully!", "success")
    else:
        flash("Subject not found!", "danger")

    session_db.close()
    return redirect(url_for("subject_management"))

# === OTHER ADMIN PAGES ===
@app.route("/new_chapter", methods=["GET", "POST"])
@login_required(role="admin")
def new_chapter():
    session_db = Session()  # Create session
    subjects = session_db.query(Subject).all()  # Query subjects
    session_db.close()  # Close session

    return render_template("admin/new_chapter.html", subjects=subjects)



@app.route('/admin/new-quiz')
@login_required(role="admin")
def new_quiz():
    return render_template('admin/new_quiz.html')

@app.route('/admin/new-question')
@login_required(role="admin")
def new_question():
    return render_template('admin/new_question.html')

@app.route('/admin/manage-users')
@login_required(role="admin")
def manage_users():
    session_db = Session()
    users = session_db.query(User).all()
    session_db.close()

    return render_template('admin/manage_users.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)


