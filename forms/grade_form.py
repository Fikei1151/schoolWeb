from flask_wtf import FlaskForm
from wtforms import FloatField, HiddenField, SubmitField
from wtforms.validators import Optional

class GradeForm(FlaskForm):
    student_id = HiddenField('Student ID', validators=[Optional()])
    course_id = HiddenField('Course ID', validators=[Optional()])
    value = FloatField('Grade', validators=[Optional()])
    submit = SubmitField('Save Grade')
