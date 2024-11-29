from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from typing import List
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from forms import CreateTeacherForm, CreateStudentForm, ChooseDesignation, CreateLoginForm, CreateGradeForm, GetUSN

app = Flask(__name__)
app.config['SECRET_KEY'] = "d297744219d80b07436ff5f8bd0ddde21d5596d89a023dfa24ae8a24729718e6"
ckeditor = CKEditor(app)
Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250))
    email: Mapped[str] = mapped_column(String(250), unique=True)
    designation: Mapped[str] = mapped_column(String(100))
    usn: Mapped[str] = mapped_column(String(100), nullable=True)
    semester: Mapped[int] = mapped_column(Integer, nullable=True)
    course: Mapped[str] = mapped_column(String(250), nullable=True)
    section: Mapped[str] = mapped_column(String(100), nullable=True)
    password: Mapped[str] = mapped_column(String(1000))
    grades: Mapped[List["UserGrade"]] = relationship(back_populates='student')


class UserGrade(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(250))
    subject_code: Mapped[str] = mapped_column(String(250))
    student_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    student: Mapped["User"] = relationship(back_populates='grades')
    internal_marks: Mapped[int] = mapped_column(Integer)
    external_marks: Mapped[int] = mapped_column(Integer)
    subject_credits: Mapped[int] = mapped_column(Integer)
    semester: Mapped[int] = mapped_column(Integer)
    remarks: Mapped[str] = mapped_column(String(1000), nullable=True)
    is_pass: Mapped[str] = mapped_column(String[10])


with app.app_context():
    db.create_all()


def assign_grade_points(n):
    if n >= 90:
        return 10
    elif n >= 80:
        return 9
    elif n >= 70:
        return 8
    elif n >= 60:
        return 7
    elif n >= 50:
        return 6
    elif n >= 45:
        return 5
    elif n >= 40:
        return 4
    else:
        return 0


def generate_report(user: User):
    semesters = []
    for i in range(1, 9):
        for sub in user.grades:
            if sub.semester == i:
                semesters.append(i)
                break
    report = {}
    cgpa = 0
    backlogs = 0
    for sem in semesters:
        cred = 0
        t_creds = 0
        for sub in user.grades:
            if sub.semester == sem:
                cred += assign_grade_points(sub.internal_marks + sub.external_marks) * sub.subject_credits
                t_creds += sub.subject_credits
                if is_pass(sub.internal_marks, sub.external_marks) == 'F':
                    backlogs += 1
        report[sem] = round((cred / t_creds), 2)
        cgpa += cred / t_creds
    report['cgpa'] = round((cgpa / len(semesters)), 2)
    report['backlogs'] = backlogs
    report['semesters'] = semesters
    return report


def is_pass(i_marks, e_marks):
    total = i_marks + e_marks
    if total >= 40 and i_marks >= 18 and e_marks >= 18:
        return 'P'
    else:
        return 'F'


def teacher_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.designation == 'Teacher':
            return function(*args, **kwargs)
        else:
            return abort(403)

    return wrapper_function


def student_specific(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.designation == 'Teacher':
            return function(*args, **kwargs)
        elif (current_user.is_authenticated and current_user.designation == 'Student' and
              current_user.usn == request.args.get('usn').upper()):
            return function(*args, **kwargs)
        else:
            return abort(403)

    return wrapper_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated and current_user.designation == 'Teacher':
        form = GetUSN()
        if form.validate_on_submit():
            return redirect(url_for('show_grades', usn=form.usn.data.upper()))
        return render_template('index.html', form=form)
    else:
        return render_template('index.html')


@app.route('/choose-designation', methods=["GET", "POST"])
def choose_designation():
    form = ChooseDesignation()
    if form.validate_on_submit():
        return redirect(url_for('register', designation=form.designation.data))
    return render_template('register.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    designation = request.args.get('designation')
    if designation == 'Teacher':
        form = CreateTeacherForm()
    elif designation == 'Student':
        form = CreateStudentForm()
    else:
        abort(403)
    if form.validate_on_submit():
        if db.session.execute(db.select(User).where(User.email == form.email.data)).scalar() is not None:
            flash("That email id is already in use. Log in instead!")
            return redirect(url_for('login'))
        if designation == 'Student':
            if db.session.execute(db.select(User).where(User.usn == form.usn.data.upper())).scalar() is not None:
                flash("That USN is already in use. Log in instead!")
                return redirect(url_for('login'))
        new_user = User()
        new_user.name = form.name.data
        new_user.email = form.email.data
        new_user.password = generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
        if designation == 'Student':
            new_user.designation = 'Student'
            new_user.section = form.section.data
            new_user.usn = form.usn.data.upper()
            new_user.semester = form.semester.data
            new_user.course = form.course.data
        elif designation == 'Teacher':
            new_user.designation = 'Teacher'
            new_user.usn = None
            new_user.section = None
            new_user.semester = None
            new_user.course = None
        db.session.add(new_user)
        db.session.commit()
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        login_user(user)
        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = CreateLoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("Invalid credentials.")
                return redirect(url_for('login'))
        else:
            flash("User does not exist.")
            return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/add_grade', methods=['GET', 'POST'])
@teacher_only
def add_grade():
    form = CreateGradeForm()
    if form.validate_on_submit():
        grade = UserGrade(
            subject=form.subject_name.data,
            subject_code=form.subject_code.data.upper(),
            student=db.session.execute(db.select(User).where(User.usn == form.usn.data.upper())).scalar(),
            internal_marks=form.internal_marks.data,
            external_marks=form.external_marks.data,
            subject_credits=form.subject_credits.data,
            semester=form.semester.data,
            is_pass=is_pass(form.internal_marks.data, form.external_marks.data),
        )
        if form.remarks.data is not None:
            grade.remarks = form.remarks.data
        else:
            grade.remarks = None
        db.session.add(grade)
        db.session.commit()
        return redirect(url_for('add_grade'))
    return render_template('add_grade.html', form=form)


@app.route('/grades')
@student_specific
def show_grades():
    user = db.session.execute(db.select(User).where(User.usn == request.args.get('usn'))).scalar()
    semesters = []
    for i in range(1, 9):
        for sub in user.grades:
            if sub.semester == i:
                semesters.append(i)
                break
    return render_template('grades.html', user=user, semesters=semesters)


@app.route('/edit_grade', methods=['GET', 'POST'])
@teacher_only
def edit_grade():
    grade = db.get_or_404(UserGrade, request.args.get('id'))
    form = CreateGradeForm(
        usn=grade.student.usn,
        semester=grade.semester,
        subject_name=grade.subject,
        subject_code=grade.subject_code,
        internal_marks=grade.internal_marks,
        external_marks=grade.external_marks,
        subject_credits=grade.subject_credits,
        remarks=grade.remarks,
    )
    if form.validate_on_submit():
        grade.student = db.session.execute(db.select(User).where(User.usn == form.usn.data.upper())).scalar()
        grade.student_id = db.session.execute(db.select(User).where(User.usn == form.usn.data.upper())).scalar().id
        grade.semester = form.semester.data
        grade.subject = form.subject_name.data
        grade.subject_code = form.subject_code.data
        grade.internal_marks = form.internal_marks.data
        grade.external_marks = form.external_marks.data
        grade.subject_credits = form.subject_credits.data
        grade.remarks = form.remarks.data
        grade.is_pass = is_pass(form.internal_marks.data, form.external_marks.data)
        db.session.commit()
        return redirect(url_for('show_grades', usn=grade.student.usn))
    return render_template('add_grade.html', form=form)


@app.route('/delete')
@teacher_only
def delete():
    grade = db.get_or_404(UserGrade, request.args.get('id'))
    usn = grade.student.usn
    db.session.delete(grade)
    db.session.commit()
    return redirect(url_for('show_grades', usn=usn))


@app.route('/report', methods=['GET', 'POST'])
@student_specific
def show_report():
    if request.method == 'POST':
        student = db.session.execute(db.select(User).where(User.usn == request.form['usn'].upper())).scalar()
    else:
        student = db.session.execute(db.select(User).where(User.usn == request.args.get('usn').upper())).scalar()
    report = generate_report(student)
    return render_template('report.html', report=report)


if __name__ == "__main__":
    app.run(debug=True)
