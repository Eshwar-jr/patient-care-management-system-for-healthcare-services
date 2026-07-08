from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, BooleanField, IntegerField, DateField, TimeField, TextAreaField
from wtforms.validators import DataRequired, Email, Length
from wtforms.fields import DecimalField

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

class PatientForm(FlaskForm):

    full_name = StringField(
        "Full Name",
        validators=[DataRequired()]
    )

    age = IntegerField(
        "Age",
        validators=[DataRequired()]
    )

    gender = SelectField(
        "Gender",
        choices=[
            ("Male","Male"),
            ("Female","Female"),
            ("Other","Other")
        ]
    )

    phone = StringField(
        "Phone",
        validators=[DataRequired()]
    )

    address = StringField(
        "Address",
        validators=[DataRequired()]
    )

    blood_group = SelectField(
        "Blood Group",
        choices=[
            ("A+","A+"),
            ("A-","A-"),
            ("B+","B+"),
            ("B-","B-"),
            ("AB+","AB+"),
            ("AB-","AB-"),
            ("O+","O+"),
            ("O-","O-")
        ]
    )

    disease = StringField(
        "Disease",
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Patient")


class AppointmentForm(FlaskForm):

    patient = SelectField(
        "Patient",
        coerce=int,
        validators=[DataRequired()]
    )

    doctor_name = StringField(
        "Doctor Name",
        validators=[DataRequired()]
    )

    appointment_date = DateField(
        "Appointment Date",
        format="%Y-%m-%d",
        validators=[DataRequired()]
    )

    appointment_time = TimeField(
        "Appointment Time",
        format="%H:%M",
        validators=[DataRequired()]
    )

    reason = StringField(
        "Reason",
        validators=[DataRequired()]
    )

    submit = SubmitField("Book Appointment")


class TreatmentForm(FlaskForm):

    patient = SelectField(
        "Patient",
        coerce=int,
        validators=[DataRequired()]
    )

    diagnosis = StringField(
        "Diagnosis",
        validators=[DataRequired()]
    )

    medicines = StringField(
        "Medicines",
        validators=[DataRequired()]
    )

    notes = TextAreaField(
        "Notes"
    )

    date = DateField(
        "Treatment Date",
        format="%Y-%m-%d",
        validators=[DataRequired()]
    )

    submit = SubmitField(
        "Save Treatment"
    )

class BillingForm(FlaskForm):

    patient = SelectField(
        "Patient",
        coerce=int,
        validators=[DataRequired()]
    )

    amount = DecimalField(
        "Amount",
        validators=[DataRequired()]
    )

    payment_status = SelectField(
        "Payment Status",
        choices=[
            ("Pending", "Pending"),
            ("Paid", "Paid")
        ]
    )

    bill_date = DateField(
        "Bill Date",
        format="%Y-%m-%d",
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Bill")