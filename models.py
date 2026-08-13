from datetime import datetime, date
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
    role = db.Column(db.String(20), nullable=False, index=True)
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

    aadhaar = db.Column(db.String(12), unique=True, nullable=True)

    email = db.Column(db.String(120), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)




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

    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id", ondelete="SET NULL"), nullable=True)
    bill = db.relationship("Bill", backref="treatments")

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

    payment_method = db.Column(
        db.String(50),
        nullable=True
    )

    payment_date = db.Column(
        db.Date,
        nullable=True
    )

class EHR(db.Model):
    __tablename__ = "ehrs"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )
    medical_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    blood_pressure = db.Column(db.String(30))
    heart_rate = db.Column(db.String(30))
    temperature = db.Column(db.String(30))
    weight = db.Column(db.String(30))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    patient = db.relationship("Patient", backref="ehrs")
    doctor = db.relationship("User", foreign_keys=[doctor_id])

class Consultation(db.Model):
    __tablename__ = "consultations"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    consultation_date = db.Column(db.Date, nullable=False, default=date.today)
    symptoms = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref="consultations")
    doctor = db.relationship("User", foreign_keys=[doctor_id])
    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id", ondelete="SET NULL"), nullable=True)
    bill = db.relationship("Bill", backref="consultations")

class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    medication_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text)
    date_prescribed = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref="prescriptions")
    doctor = db.relationship("User", foreign_keys=[doctor_id])

class LabReport(db.Model):
    __tablename__ = "lab_reports"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )
    requested_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    performed_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )
    test_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(30), default="Pending")
    results = db.Column(db.Text)
    lab_notes = db.Column(db.Text)
    request_date = db.Column(db.Date, nullable=False, default=date.today)
    result_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref="lab_reports")
    requested_by = db.relationship("User", foreign_keys=[requested_by_id])
    performed_by = db.relationship("User", foreign_keys=[performed_by_id])
    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id", ondelete="SET NULL"), nullable=True)
    bill = db.relationship("Bill", backref="lab_reports")


class Medicine(db.Model):
    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=True)
    batch_number = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    expiry_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DispensingRecord(db.Model):
    __tablename__ = "dispensing_records"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    dispensed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    dispensed_date = db.Column(db.Date, nullable=False, default=date.today)
    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref="dispensed_medicines")
    medicine = db.relationship("Medicine", backref="dispensing_records")
    dispensed_by = db.relationship("User", foreign_keys=[dispensed_by_id])
    bill = db.relationship("Bill", backref="dispensing_records")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Unread", index=True)
    delivery_status = db.Column(db.String(20), nullable=False, default="Pending")
    related_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="notifications")


class LoginActivity(db.Model):
    __tablename__ = "login_activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(30), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(20), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="login_activities")


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey("consultations.id"), nullable=True, index=True)

    doctor_rating = db.Column(db.Integer, nullable=False, default=5)
    hospital_rating = db.Column(db.Integer, nullable=False, default=5)
    lab_rating = db.Column(db.Integer, nullable=False, default=5)
    pharmacy_rating = db.Column(db.Integer, nullable=False, default=5)

    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient", backref="feedbacks")
    doctor = db.relationship("User", foreign_keys=[doctor_id])
    consultation = db.relationship("Consultation", backref="feedbacks")

    @property
    def overall_rating(self):
        return round((self.doctor_rating + self.hospital_rating + self.lab_rating + self.pharmacy_rating) / 4.0, 1)




