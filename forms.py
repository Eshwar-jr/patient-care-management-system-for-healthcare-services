from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length


class RegistrationForm(FlaskForm):

    full_name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(max=100)]
    )

    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=50)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    phone = StringField(
        "Phone Number",
        validators=[DataRequired(), Length(min=10, max=15)]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)]
    )

    role = SelectField(
        "Role",
        choices=[
            ("Patient", "Patient"),
            ("Doctor", "Doctor"),
            ("Nurse", "Nurse"),
            ("Admin", "Admin")
        ]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    remember = BooleanField("Remember Me")

    submit = SubmitField("Login")