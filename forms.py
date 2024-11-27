from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, DecimalField, IntegerField
from wtforms.validators import DataRequired, URL, InputRequired, Email
from flask_ckeditor import CKEditorField
from config import semesters, courses, section, designation


class CreateStudentForm(FlaskForm):
    name = StringField('Name:', validators=[InputRequired('Field cannot be empty.')])
    email = StringField('Email:', validators=[InputRequired('Field cannot be empty.'), Email('Enter a valid email.')])
    usn = StringField('USN:', validators=[InputRequired('Field cannot be empty.')])
    semester = SelectField('Semester:', choices=semesters)
    course = SelectField('Course:', choices=courses)
    section = SelectField('Section:', choices=section)
    password = PasswordField('Password:', validators=[InputRequired()])
    submit = SubmitField('Register')


class CreateTeacherForm(FlaskForm):
    name = StringField('Name:', validators=[InputRequired('Field cannot be empty.')])
    email = StringField('Email:', validators=[InputRequired('Field cannot be empty.'), Email('Enter a valid email.')])
    password = PasswordField('Password:', validators=[InputRequired('Field cannot be empty.')])
    submit = SubmitField('Register')


class ChooseDesignation(FlaskForm):
    designation = SelectField('Designation', choices=designation)
    submit = SubmitField('Select')


class CreateLoginForm(FlaskForm):
    email = StringField('Email:', validators=[InputRequired('Field cannot be empty.'), Email('Enter a valid email.')])
    password = PasswordField('Password:', validators=[InputRequired('Field cannot be empty.')])
    submit = SubmitField('Log In')


class CreateGradeForm(FlaskForm):
    usn = StringField('USN:', validators=[InputRequired('Field cannot be empty.')])
    semester = IntegerField('Semester:', validators=[InputRequired('Field cannot be empty.')])
    subject_name = StringField('Subject name:', validators=[InputRequired('Field cannot be empty.')])
    subject_code = StringField('Subject Code:', validators=[InputRequired('Field cannot be empty.')])
    internal_marks = IntegerField('Internal Score:', validators=[InputRequired('Field cannot be empty.')])
    external_marks = IntegerField('External Score:', validators=[InputRequired('Field cannot be empty.')])
    subject_credits = IntegerField('Subject Credits:', validators=[InputRequired('Field cannot be empty.')])
    submit = SubmitField('Add Record')


class GetUSN(FlaskForm):
    usn = StringField('USN:', validators=[InputRequired('Field cannot be empty.')])
    submit = SubmitField('Search Grades')