from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField, TextAreaField, RadioField
from wtforms.validators import DataRequired,Email,EqualTo, Length
from wtforms import ValidationError


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('pass_confirm', message='Passwords Must Match!')])
    pass_confirm = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register!')




class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class SearchForm(FlaskForm):
    search = StringField('', validators=[DataRequired()])
    submit = SubmitField('Search')

class ReviewForm(FlaskForm):
    review = TextAreaField('',validators=[DataRequired(), Length(min=10)])
    ratings = RadioField('Book Rating', choices=[(1,'1'), (2,'2'), (3,'3'), (4,'4'), (5,'5')])
    submit = SubmitField()
