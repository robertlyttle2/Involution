from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    choice = SelectField(label="Choose an option",
                         choices=["Movies", "TV Shows"])
    title = StringField(label="Search for a movie...",
                        validators=[DataRequired()])
    search = SubmitField(label="Search")


class RegisterForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Sign Up")


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Login")


class ChangePassword(FlaskForm):
    current_password = PasswordField(
        label="Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        label="New Password", validators=[DataRequired()])
    confirm_new_password = PasswordField(
        label="Confirm New Password", validators=[DataRequired()])
    submit = SubmitField(label="Submit")
