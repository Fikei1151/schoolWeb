from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired()])
    code = StringField('Course Code', validators=[DataRequired()])
    credit = IntegerField('Credit', validators=[DataRequired()])
    description = TextAreaField('Course Description', validators=[DataRequired()])
    submit = SubmitField('Add Course')
