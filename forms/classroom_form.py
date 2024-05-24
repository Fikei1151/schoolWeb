from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired

class ClassroomForm(FlaskForm):
    name = StringField('Classroom Name', validators=[DataRequired()])
    academic_year = StringField('Academic Year', validators=[DataRequired()])
    submit = SubmitField('Add Classroom')
