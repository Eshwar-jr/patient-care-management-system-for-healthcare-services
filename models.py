from datetime import datetime
from flask_login import UserMixin
from extensions import db
from extensions import login_manager

class User(UserMixin, db.Model):

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def __repr__(self):
   return f"<User {self.username}>"
    
class Patient(db.Model):

    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    age = db.Column(db.Integer)

    gender = db.Column(db.String(20))

    phone = db.Column(db.String(15))

    address = db.Column(db.String(200))

    blood_group = db.Column(db.String(10))

    disease = db.Column(db.String(100))


class Appointment(db.Model):

    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    patient = db.relationship(
        "Patient",
        backref="appointments"
    )

    doctor_name = db.Column(db.String(100))
    appointment_date = db.Column(db.Date)
    appointment_time = db.Column(db.Time)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(30), default="Scheduled")

    doctor_name = db.Column(
        db.String(100),
        nullable=False
    )

    appointment_date = db.Column(
        db.Date,
        nullable=False
    )

    appointment_time = db.Column(
        db.Time,
        nullable=False
    )

    reason = db.Column(
        db.String(255)
    )

    status = db.Column(
        db.String(30),
        default="Scheduled"
    )
    status = db.Column(
    db.String(20),
    default="Booked"
    )

class Treatment(db.Model):

    __tablename__ = "treatments"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    patient = db.relationship(
        "Patient",
        backref="treatments"
    )

    diagnosis = db.Column(
        db.String(200),
        nullable=False
    )

    medicines = db.Column(
        db.String(300),
        nullable=False
    )

    notes = db.Column(
        db.String(500)
    )

    date = db.Column(
        db.Date,
        nullable=False
    )

class Bill(db.Model):

    __tablename__ = "bills"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    patient = db.relationship(
        "Patient",
        backref="bills"
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    payment_status = db.Column(
        db.String(30),
        default="Pending"
    )

    bill_date = db.Column(
        db.Date,
        nullable=False
    )