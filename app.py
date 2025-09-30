from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///vidyarth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# =========================
# Database Models
# =========================
# --- Models ---
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vidyarth.db'
db = SQLAlchemy(app)

# =========================
# MODELS
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'faculty', 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class StudentData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gpa = db.Column(db.Float, default=0)
    attendance = db.Column(db.Float, default=0)
    pending_fees = db.Column(db.Float, default=0)
    books_issued = db.Column(db.Integer, default=0)

class LibraryBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100))
    issued_date = db.Column(db.String(20))
    due_date = db.Column(db.String(20))
    returned = db.Column(db.Boolean, default=False)

class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String(50))
    amount = db.Column(db.Float)
    paid = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.String(20))

class Performance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.String(20))
    gpa = db.Column(db.Float)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.String(20))
    percentage = db.Column(db.Float)

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(200))
    name = db.Column(db.String(100))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    roll_no = db.Column(db.String(20))

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50))
    date = db.Column(db.String(20))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    marks = db.Column(db.Integer)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    due_date = db.Column(db.String(20))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    submitted = db.Column(db.Boolean, default=False)

# =========================
# ROUTES
# =========================
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!', 'success')
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            elif user.role == 'faculty':
                return redirect(url_for('faculty_dashboard'))
            else:
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------------
# Student Dashboard
# ------------------------
@app.route('/student')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    student_data = StudentData.query.filter_by(student_id=student_id).first()
    fees = Fee.query.filter_by(student_id=student_id).all()
    library_books = LibraryBook.query.filter_by(student_id=student_id).all()
    performance = Performance.query.filter_by(student_id=student_id).all()
    attendance_records = Attendance.query.filter_by(student_id=student_id).all()
    
    performance_dates = [p.date for p in performance]
    gpa_over_time = [p.gpa for p in performance]
    attendance_dates = [a.date for a in attendance_records]
    attendance_over_time = [a.percentage for a in attendance_records]
    
    return render_template('student_dashboard.html',
                           student_name=User.query.get(student_id).username,
                           gpa=student_data.gpa,
                           attendance_percent=student_data.attendance,
                           pending_fees=student_data.pending_fees,
                           books_issued=student_data.books_issued,
                           fees=fees,
                           library_books=library_books,
                           performance_dates=performance_dates,
                           gpa_over_time=gpa_over_time,
                           attendance_dates=attendance_dates,
                           attendance_over_time=attendance_over_time)

# ------------------------
# Faculty Dashboard
# ------------------------
@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'user_id' not in session or session.get('role') != 'faculty':
        return redirect(url_for('login'))

    faculty = Faculty.query.first()
    students = Student.query.all()
    exams = Exam.query.all()
    assignments = Assignment.query.all()

    # --- Chart Data ---
    # Marks distribution
    marks_a = len([e for e in exams if e.marks >= 90])
    marks_b = len([e for e in exams if 80 <= e.marks < 90])
    marks_c = len([e for e in exams if 70 <= e.marks < 80])
    marks_d = len([e for e in exams if 60 <= e.marks < 70])
    marks_f = len([e for e in exams if e.marks < 60])

    # Assignment trend over dates
    assignment_dates = sorted(list({a.due_date for a in assignments}))
    assignment_submitted = [len([a for a in assignments if a.due_date == d and a.submitted]) for d in assignment_dates]

    return render_template('faculty_dashboard.html',
                           faculty_name=faculty.name,
                           total_students=len(students),
                           upcoming_exams=len([e for e in exams if e.date >= date.today().isoformat()]),
                           pending_assignments=len([a for a in assignments if not a.submitted]),
                           marks_uploaded=len([e for e in exams if e.marks is not None]),
                           exams=exams,
                           assignments=assignments,
                           # Chart data
                           marks_a=marks_a,
                           marks_b=marks_b,
                           marks_c=marks_c,
                           marks_d=marks_d,
                           marks_f=marks_f,
                           assignment_dates=assignment_dates,
                           assignment_submitted=assignment_submitted)


# ------------------------
# Admin Dashboard
# ------------------------
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    students = User.query.filter_by(role='student').all()
    faculty = User.query.filter_by(role='faculty').all()
    return render_template('admin_dashboard.html', students=students, faculty=faculty)

# ------------------------
# Chat Page
# ------------------------
@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', user_name=User.query.get(session['user_id']).username)

# ------------------------
# Upload Routes
# ------------------------
@app.route('/upload_student_data', methods=['GET','POST'])
def upload_student_data():
    return "Upload Student Data Page"

@app.route('/upload_marks/<int:exam_id>', methods=['GET','POST'])
def upload_marks(exam_id):
    return f"Upload marks page for exam {exam_id}"

# =========================
# CLI Command to initialize DB
# =========================
@app.cli.command('initdb')
def initdb():
    db.create_all()
    print("Database initialized!")

    # Predefined users
    student = User(username='vidyarth_student', role='student')
    student.set_password('student123')
    faculty = User(username='vidyarth_faculty', role='faculty')
    faculty.set_password('faculty123')
    admin = User(username='vidyarth_admin', role='admin')
    admin.set_password('admin123')
    db.session.add_all([student, faculty, admin])
    db.session.commit()

    # Sample student data
    student_data = StudentData(student_id=student.id, gpa=8.5, attendance=95, pending_fees=1200, books_issued=3)
    db.session.add(student_data)

    # Sample fees
    fee1 = Fee(student_id=student.id, type="Tuition Fee", amount=5000, paid=False, due_date="2025-10-10")
    fee2 = Fee(student_id=student.id, type="Lab Fee", amount=1500, paid=True, due_date="2025-09-01")
    db.session.add_all([fee1, fee2])

    # Sample library books
    book1 = LibraryBook(student_id=student.id, title="Mathematics Fundamentals", issued_date="2025-09-05", due_date="2025-10-05", returned=False)
    db.session.add(book1)

    # Sample performance & attendance
    performance_samples = [
        Performance(student_id=student.id, date="2025-07", gpa=8.0),
        Performance(student_id=student.id, date="2025-08", gpa=8.3),
        Performance(student_id=student.id, date="2025-09", gpa=8.5)
    ]
    attendance_samples = [
        Attendance(student_id=student.id, date="2025-07", percentage=90),
        Attendance(student_id=student.id, date="2025-08", percentage=92),
        Attendance(student_id=student.id, date="2025-09", percentage=95)
    ]
    db.session.add_all(performance_samples + attendance_samples)
    db.session.commit()
    print("Predefined raw data added successfully!")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
