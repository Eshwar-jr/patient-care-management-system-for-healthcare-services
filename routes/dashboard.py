from flask import render_template, redirect, url_for, flash, request
from app import app
from extensions import db
from models import Patient, Appointment, Treatment, Bill, User, EHR, Consultation, Prescription, LabReport, Medicine, DispensingRecord, Notification, LoginActivity
from forms import PatientForm, AppointmentForm, TreatmentForm, BillingForm, EHRForm, ConsultationForm, PrescriptionForm, LabReportRequestForm, LabReportResultForm, MedicineForm, DispenseForm, StockUpdateForm, RecordPaymentForm
from flask_login import login_required, current_user
from datetime import date, timedelta
from decimal import Decimal

def get_patient_for_user(user):
    patient = None
    if user.phone:
        patient = Patient.query.filter_by(phone=user.phone).first()
    if not patient:
        patient = Patient.query.filter_by(full_name=user.full_name).first()
    if not patient:
        patient = Patient(
            full_name=user.full_name,
            phone=user.phone,
            age=None,
            gender=None,
            address=None,
            blood_group=None,
            disease=None
        )
        db.session.add(patient)
        db.session.commit()
    return patient


def get_user_id_for_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if patient and patient.email:
        user = User.query.filter_by(email=patient.email).first()
        if user:
            return user.id
    return None


def create_notification(user_id, title, message, notification_type, related_id=None):
    if not user_id:
        return None
    if related_id:
        existing = Notification.query.filter_by(
            user_id=user_id,
            notification_type=notification_type,
            related_id=related_id
        ).first()
        if existing:
            return existing
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        status="Unread",
        delivery_status="Pending",
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def trigger_billing_notification(bill):
    if bill.payment_status == "Pending":
        patient_uid = get_user_id_for_patient(bill.patient_id)
        if patient_uid:
            msg = f"Billing payment reminder: INR {bill.amount:.2f} is outstanding for your record."
            create_notification(patient_uid, "Billing Reminder", msg, "Billing", related_id=bill.id)

@app.context_processor
def inject_unread_notification_count():
    if current_user.is_authenticated:
        count = Notification.query.filter_by(user_id=current_user.id).filter(Notification.status != 'Read').count()
        return dict(unread_notification_count=count)
    return dict(unread_notification_count=0)


@app.route("/doctor")
@login_required
def doctor_dashboard():

    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()
    treatment_count = Treatment.query.count()
    bill_count = Bill.query.count()
    ehr_count = EHR.query.count()
    consultation_count = Consultation.query.count()
    prescription_count = Prescription.query.count()
    lab_count = LabReport.query.count()

    recent_patients = Patient.query.order_by(
        Patient.id.desc()
    ).limit(5).all()

    recent_appointments = Appointment.query.order_by(
        Appointment.id.desc()
    ).limit(5).all()
    chart_data = [
           patient_count,
           appointment_count,
           treatment_count,
           bill_count,
           ehr_count,
           consultation_count,
           prescription_count,
           lab_count
    ]

    return render_template(
        "doctor_dashboard.html",
        patient_count=patient_count,
        appointment_count=appointment_count,
        treatment_count=treatment_count,
        bill_count=bill_count,
        ehr_count=ehr_count,
        consultation_count=consultation_count,
        prescription_count=prescription_count,
        lab_count=lab_count,
        recent_patients=recent_patients,
        recent_appointments=recent_appointments,
        today=date.today(),
        chart_data=chart_data
    )


@app.route("/patient/add", methods=["GET", "POST"])
@login_required
def add_patient():
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    form = PatientForm()

    if form.validate_on_submit():
        if form.aadhaar.data:
            existing_aadhaar = Patient.query.filter_by(aadhaar=form.aadhaar.data).first()
            if existing_aadhaar:
                flash("A patient with this Aadhaar Number already exists.", "danger")
                return render_template("add_patient.html", form=form)

        patient = Patient(
            full_name=form.full_name.data,
            age=form.age.data,
            gender=form.gender.data,
            phone=form.phone.data,
            address=form.address.data,
            blood_group=form.blood_group.data,
            disease=form.disease.data,
            email=form.email.data,
            aadhaar=form.aadhaar.data
        )

        db.session.add(patient)
        db.session.commit()

        flash("Patient added successfully!", "success")

        return redirect(url_for("doctor_dashboard"))

    return render_template(
        "add_patient.html",
        form=form
    )

@app.route("/patient/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_patient(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    patient = Patient.query.get_or_404(id)

    form = PatientForm(obj=patient)

    if form.validate_on_submit():
        if form.aadhaar.data:
            existing_aadhaar = Patient.query.filter_by(aadhaar=form.aadhaar.data).first()
            if existing_aadhaar and existing_aadhaar.id != patient.id:
                flash("A patient with this Aadhaar Number already exists.", "danger")
                return render_template("edit_patient.html", form=form)

        patient.full_name = form.full_name.data
        patient.age = form.age.data
        patient.gender = form.gender.data
        patient.phone = form.phone.data
        patient.address = form.address.data
        patient.blood_group = form.blood_group.data
        patient.disease = form.disease.data
        patient.email = form.email.data
        patient.aadhaar = form.aadhaar.data

        db.session.commit()

        flash("Patient updated successfully!", "success")

        return redirect(url_for("patients"))

    return render_template(
        "edit_patient.html",
        form=form
    )

@app.route("/patient/delete/<int:id>")
@login_required
def delete_patient(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    patient = Patient.query.get_or_404(id)

    db.session.delete(patient)
    db.session.commit()

    flash("Patient deleted successfully!", "success")

    return redirect(url_for("patients"))


@app.route("/patient/<int:id>")
@login_required
def patient_profile(id):
    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        if patient.id != id:
            flash("Access denied.", "danger")
            return redirect(url_for("patient_profile_view"))

    patient = Patient.query.get_or_404(id)

    return render_template(
        "patient_profile.html",
        patient=patient
    )


@app.route("/patient")
@login_required
def patient_dashboard():
    if current_user.role.lower() != 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    patient = get_patient_for_user(current_user)

    # Metrics
    appointment_count = Appointment.query.filter_by(patient_id=patient.id).count()
    treatment_count = Treatment.query.filter_by(patient_id=patient.id).count()
    bill_count = Bill.query.filter_by(patient_id=patient.id).count()
    ehr_count = EHR.query.filter_by(patient_id=patient.id).count()
    consultation_count = Consultation.query.filter_by(patient_id=patient.id).count()
    prescription_count = Prescription.query.filter_by(patient_id=patient.id).count()
    lab_count = LabReport.query.filter_by(patient_id=patient.id).count()

    # Upcoming Appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.status.in_(["Booked", "Scheduled"])
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).limit(5).all()

    # Recent Treatments
    recent_treatments = Treatment.query.filter_by(patient_id=patient.id).order_by(Treatment.date.desc()).limit(5).all()

    # Bills
    bills = Bill.query.filter_by(patient_id=patient.id).order_by(Bill.bill_date.desc()).all()

    return render_template(
        "patient_dashboard.html",
        patient=patient,
        appointment_count=appointment_count,
        treatment_count=treatment_count,
        bill_count=bill_count,
        ehr_count=ehr_count,
        consultation_count=consultation_count,
        prescription_count=prescription_count,
        lab_count=lab_count,
        upcoming_appointments=upcoming_appointments,
        recent_treatments=recent_treatments,
        bills=bills,
        today=date.today()
    )


@app.route("/patient/profile", methods=["GET", "POST"])
@login_required
def patient_profile_view():
    if current_user.role.lower() != 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    patient = get_patient_for_user(current_user)

    if request.method == "POST":
        phone = request.form.get("phone")
        address = request.form.get("address")
        email = request.form.get("email")

        if not phone or not address or not email:
            flash("Phone, address, and email are required.", "danger")
        else:
            email_check = User.query.filter(User.email == email, User.id != current_user.id).first()
            if email_check:
                flash("Email address is already in use by another user.", "danger")
            else:
                current_user.phone = phone
                current_user.email = email
                patient.phone = phone
                patient.address = address
                db.session.commit()
                flash("Profile updated successfully!", "success")
                return redirect(url_for("patient_profile_view"))

    return render_template(
        "patient_profile.html",
        patient=patient,
        user=current_user
    )

@app.route("/patients")
@login_required
def patients():
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    search = request.args.get("search")

    if search:

        patients = Patient.query.filter(
            Patient.full_name.contains(search)
        ).all()

    else:

        patients = Patient.query.all()

    return render_template(
        "patients.html",
        patients=patients
    )

@app.route("/appointments/add", methods=["GET", "POST"])
@login_required
def add_appointment():
    form = AppointmentForm()
    
    is_patient = current_user.role.lower() == 'patient'
    patient = None
    
    if is_patient:
        patient = get_patient_for_user(current_user)
        form.patient.choices = [(patient.id, patient.full_name)]
        form.patient.data = patient.id
    else:
        patients = Patient.query.all()
        form.patient.choices = [(p.id, p.full_name) for p in patients]

    doctors = User.query.filter(User.role.ilike('doctor')).all()

    if form.validate_on_submit():
        appointment = Appointment(
            patient_id=form.patient.data,
            doctor_name=form.doctor_name.data,
            appointment_date=form.appointment_date.data,
            appointment_time=form.appointment_time.data,
            reason=form.reason.data,
            status="Booked" if is_patient else "Scheduled"
        )
        db.session.add(appointment)
        db.session.commit()

        # Trigger notifications
        patient_uid = get_user_id_for_patient(appointment.patient_id)
        msg_patient = f"Your appointment is scheduled with Dr. {appointment.doctor_name} on {appointment.appointment_date} at {appointment.appointment_time}."
        create_notification(patient_uid, "Appointment Scheduled", msg_patient, "Appointment", related_id=appointment.id)

        doctor = User.query.filter(User.role.ilike('doctor'), User.full_name == appointment.doctor_name).first()
        if doctor:
            msg_doc = f"New appointment scheduled with Patient {appointment.patient.full_name} on {appointment.appointment_date} at {appointment.appointment_time}."
            create_notification(doctor.id, "New Appointment Assigned", msg_doc, "Appointment", related_id=appointment.id)

        flash("Appointment booked successfully!", "success")
        return redirect(url_for("appointments"))

    return render_template(
        "add_appointment.html",
        form=form,
        doctors=doctors,
        patient_id=patient.id if is_patient else None
    )

@app.route("/appointments")
@login_required
def appointments():
    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    else:
        patient_id = request.args.get('patient_id')
        if patient_id:
            appointments = Appointment.query.filter_by(patient_id=patient_id).all()
        else:
            appointments = Appointment.query.all()

    return render_template(
        "appointments.html",
        appointments=appointments
    )

@app.route("/appointments/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_appointment(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    appointment = Appointment.query.get_or_404(id)

    if appointment.status == "Completed":
        flash("Completed appointments cannot be edited.", "danger")
        return redirect(url_for("appointments"))

    form = AppointmentForm(obj=appointment)

    form.patient.choices = [
        (p.id, p.full_name)
        for p in Patient.query.all()
    ]

    if form.validate_on_submit():
        appointment.patient_id = form.patient.data
        appointment.doctor_name = form.doctor_name.data
        appointment.appointment_date = form.appointment_date.data
        appointment.appointment_time = form.appointment_time.data
        appointment.reason = form.reason.data
        appointment.status = request.form["status"]
        db.session.commit()
        flash("Appointment updated successfully!", "success")
        return redirect(url_for("appointments"))

    return render_template(
        "edit_appointment.html",
        form=form,
        appointment=appointment
    )

@app.route("/appointments/delete/<int:id>")
@login_required
def delete_appointment(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    appointment = Appointment.query.get_or_404(id)

    if appointment.status == "Completed":
        flash("Completed appointments cannot be deleted.", "danger")
        return redirect(url_for("appointments"))

    db.session.delete(appointment)
    db.session.commit()

    flash("Appointment deleted successfully!", "success")
    return redirect(url_for("appointments"))

@app.route("/appointments/cancel/<int:id>")
@login_required
def cancel_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    
    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        if appointment.patient_id != patient.id:
            flash("You are not authorized to cancel this appointment.", "danger")
            return redirect(url_for("appointments"))
            
    if appointment.status == "Completed":
        flash("Completed appointments cannot be cancelled.", "danger")
        return redirect(url_for("appointments"))
        
    appointment.status = "Cancelled"
    db.session.commit()
    flash("Appointment cancelled successfully!", "success")
    return redirect(request.referrer or url_for("appointments"))

#TREATMENTS

@app.route("/treatments")
@login_required
def treatments():
    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        treatments = Treatment.query.filter_by(patient_id=patient.id).all()
    else:
        treatments = Treatment.query.all()

    return render_template(
        "treatments.html",
        treatments=treatments
    )

@app.route("/treatments/add", methods=["GET", "POST"])
@login_required
def add_treatment():
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    form = TreatmentForm()

    form.patient.choices = [
        (p.id, p.full_name)
        for p in Patient.query.all()
    ]

    if form.validate_on_submit():
        cost = form.treatment_cost.data
        bill_id = None
        if cost and cost > 0:
            bill = Bill(
                patient_id=form.patient.data,
                amount=float(cost),
                payment_status="Pending",
                bill_date=form.date.data or date.today()
            )
            db.session.add(bill)
            db.session.flush()
            bill_id = bill.id

        treatment = Treatment(
            patient_id=form.patient.data,
            diagnosis=form.diagnosis.data,
            medicines=form.medicines.data,
            notes=form.notes.data,
            date=form.date.data,
            bill_id=bill_id
        )

        db.session.add(treatment)
        db.session.commit()

        if bill_id:
            trigger_billing_notification(bill)

        flash(
            "Treatment added successfully!",
            "success"
        )

        return redirect(url_for("treatments"))

    return render_template(
        "add_treatment.html",
        form=form
    )

@app.route("/treatments/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_treatment(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    treatment = Treatment.query.get_or_404(id)

    form = TreatmentForm(obj=treatment)

    form.patient.choices = [
        (p.id, p.full_name)
        for p in Patient.query.all()
    ]

    if form.validate_on_submit():

        treatment.patient_id = form.patient.data
        treatment.diagnosis = form.diagnosis.data
        treatment.medicines = form.medicines.data
        treatment.notes = form.notes.data
        treatment.date = form.date.data

        db.session.commit()

        flash("Treatment updated successfully!", "success")

        return redirect(url_for("treatments"))

    return render_template(
        "edit_treatment.html",
        form=form
    )

@app.route("/treatments/delete/<int:id>")
@login_required
def delete_treatment(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    treatment = Treatment.query.get_or_404(id)

    db.session.delete(treatment)

    db.session.commit()

    flash("Treatment deleted successfully!", "success")

    return redirect(url_for("treatments"))

#BILLING
@app.route("/billing")
@login_required
def billing_dashboard():
    if current_user.role.lower() == 'patient':
        flash("Access denied. Patients cannot access the Billing Dashboard.", "danger")
        return redirect(url_for("patient_dashboard"))

    today_date = date.today()
    overdue_limit = today_date - timedelta(days=14)

    # Sum calculations using Decimal to avoid rounding issues
    total_revenue = db.session.query(db.func.sum(Bill.amount)).filter_by(payment_status="Paid").scalar() or 0.0
    total_pending = db.session.query(db.func.sum(Bill.amount)).filter_by(payment_status="Pending").scalar() or 0.0
    total_overdue = db.session.query(db.func.sum(Bill.amount)).filter(Bill.payment_status == "Pending", Bill.bill_date <= overdue_limit).scalar() or 0.0

    total_bills = Bill.query.count()
    paid_count = Bill.query.filter_by(payment_status="Paid").count()
    pending_count = Bill.query.filter_by(payment_status="Pending").count()
    overdue_count = Bill.query.filter(Bill.payment_status == "Pending", Bill.bill_date <= overdue_limit).count()

    recent_bills = Bill.query.order_by(Bill.id.desc()).limit(10).all()

    return render_template(
        "billing_dashboard.html",
        total_revenue=total_revenue,
        total_pending=total_pending,
        total_overdue=total_overdue,
        total_bills=total_bills,
        paid_count=paid_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
        recent_bills=recent_bills
    )

@app.route("/bills")
@login_required
def bills():
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("search", "")

    today_date = date.today()
    overdue_limit = today_date - timedelta(days=14)

    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        query = Bill.query.filter_by(patient_id=patient.id)
    else:
        query = Bill.query

    if search_query:
        query = query.join(Patient).filter(Patient.full_name.ilike(f"%{search_query}%"))

    if status_filter == "paid":
        query = query.filter(Bill.payment_status == "Paid")
    elif status_filter == "pending":
        query = query.filter(Bill.payment_status == "Pending")
    elif status_filter == "overdue":
        query = query.filter(Bill.payment_status == "Pending", Bill.bill_date <= overdue_limit)

    bills_list = query.order_by(Bill.id.desc()).all()

    return render_template(
        "bills.html",
        bills=bills_list,
        status_filter=status_filter,
        search_query=search_query,
        overdue_limit=overdue_limit
    )

@app.route("/bills/add", methods=["GET", "POST"])
@login_required
def add_bill():
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    form = BillingForm()
    form.patient.choices = [(p.id, p.full_name) for p in Patient.query.all()]

    if form.validate_on_submit():
        bill = Bill(
            patient_id=form.patient.data,
            amount=float(form.amount.data),
            payment_status=form.payment_status.data,
            bill_date=form.bill_date.data
        )
        db.session.add(bill)
        db.session.commit()
        trigger_billing_notification(bill)
        flash("Bill added successfully!", "success")
        return redirect(url_for("bills"))

    return render_template("add_bill.html", form=form)

@app.route("/bills/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_bill(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    bill = Bill.query.get_or_404(id)
    form = BillingForm(obj=bill)
    form.patient.choices = [(p.id, p.full_name) for p in Patient.query.all()]

    if form.validate_on_submit():
        bill.patient_id = form.patient.data
        bill.amount = float(form.amount.data)
        bill.payment_status = form.payment_status.data
        bill.bill_date = form.bill_date.data
        db.session.commit()
        flash("Bill updated successfully!", "success")
        return redirect(url_for("bills"))

    return render_template("edit_bill.html", form=form)

@app.route("/bills/delete/<int:id>")
@login_required
def delete_bill(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    bill = Bill.query.get_or_404(id)
    db.session.delete(bill)
    db.session.commit()
    flash("Bill deleted successfully!", "success")
    return redirect(url_for("bills"))

@app.route("/bills/view/<int:id>")
@login_required
def view_bill(id):
    bill = Bill.query.get_or_404(id)

    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        if bill.patient_id != patient.id:
            flash("Access denied. You can only view your own bills.", "danger")
            return redirect(url_for("bills"))

    today_date = date.today()
    overdue_limit = today_date - timedelta(days=14)
    is_overdue = bill.payment_status == "Pending" and bill.bill_date <= overdue_limit

    # Resolve items associated with this bill
    items = []
    
    # Check Pharmacy DispensingRecord
    dispensings = DispensingRecord.query.filter_by(bill_id=bill.id).all()
    for d in dispensings:
        items.append({
            "name": f"Pharmacy: {d.medicine.name} (Batch: {d.medicine.batch_number or 'N/A'})",
            "quantity": d.quantity,
            "unit_price": d.unit_price,
            "total": d.total_amount
        })

    # Check Consultation
    consultations = Consultation.query.filter_by(bill_id=bill.id).all()
    for c in consultations:
        items.append({
            "name": f"Doctor Consultation: {c.diagnosis} (Dr. {c.doctor.full_name})",
            "quantity": 1,
            "unit_price": bill.amount,
            "total": bill.amount
        })

    # Check LabReport
    lab_reports = LabReport.query.filter_by(bill_id=bill.id).all()
    for l in lab_reports:
        items.append({
            "name": f"Laboratory Test: {l.test_name} (Status: {l.status})",
            "quantity": 1,
            "unit_price": bill.amount,
            "total": bill.amount
        })

    # Check Treatment
    treatments = Treatment.query.filter_by(bill_id=bill.id).all()
    for t in treatments:
        items.append({
            "name": f"Treatment Care: {t.diagnosis} - {t.medicines}",
            "quantity": 1,
            "unit_price": bill.amount,
            "total": bill.amount
        })

    # Fallback to general service if no specific items are linked
    if not items:
        items.append({
            "name": "General Medical Service / Consultation Fee",
            "quantity": 1,
            "unit_price": bill.amount,
            "total": bill.amount
        })

    return render_template(
        "view_bill.html",
        bill=bill,
        items=items,
        is_overdue=is_overdue
    )

@app.route("/bills/pay/<int:id>", methods=["GET", "POST"])
@login_required
def record_payment(id):
    if current_user.role.lower() not in ["admin"]:
        flash("Access denied. Only administrators are authorized to record payments.", "danger")
        return redirect(url_for("bills"))

    bill = Bill.query.get_or_404(id)

    if bill.payment_status == "Paid":
        flash("This bill has already been paid.", "warning")
        return redirect(url_for("view_bill", id=bill.id))

    form = RecordPaymentForm()
    if request.method == "GET" and not form.payment_date.data:
        form.payment_date.data = date.today()

    if form.validate_on_submit():
        bill.payment_status = "Paid"
        bill.payment_method = form.payment_method.data
        bill.payment_date = form.payment_date.data
        db.session.commit()
        flash("Payment recorded successfully!", "success")
        return redirect(url_for("view_bill", id=bill.id))

    return render_template("record_payment.html", form=form, bill=bill)


#doctor management

@app.route("/doctors")
@login_required
def doctors():

    doctors = User.query.filter_by(role="doctor").all()

    return render_template(
        "doctors.html",
        doctors=doctors
    )

@app.route("/doctors/delete/<int:id>")
@login_required
def delete_doctor(id):

    doctor = User.query.get_or_404(id)

    db.session.delete(doctor)
    db.session.commit()

    flash("Doctor deleted successfully!", "success")

    return redirect(url_for("doctors"))

@app.route("/doctors/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_doctor(id):

    doctor = User.query.get_or_404(id)

    if request.method == "POST":

        doctor.full_name = request.form["full_name"]
        doctor.username = request.form["username"]
        doctor.email = request.form["email"]
        doctor.phone = request.form["phone"]

        db.session.commit()

        flash("Doctor updated successfully!", "success")

        return redirect(url_for("doctors"))

    return render_template(
        "edit_doctor.html",
        doctor=doctor
    )

@app.route("/nurses")
@login_required
def nurses():

    nurses = User.query.filter_by(role="nurse").all()

    return render_template(
        "nurses.html",
        nurses=nurses
    )
@app.route("/nurse/dashboard")
@login_required
def nurse_dashboard():

    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()
    treatment_count = Treatment.query.count()
    ehr_count = EHR.query.count()
    consultation_count = Consultation.query.count()
    prescription_count = Prescription.query.count()
    lab_count = LabReport.query.count()

    recent_patients = Patient.query.order_by(
        Patient.id.desc()
    ).limit(5).all()

    recent_appointments = Appointment.query.order_by(
        Appointment.id.desc()
    ).limit(5).all()

    return render_template(
        "nurse_dashboard.html",
        patient_count=patient_count,
        appointment_count=appointment_count,
        treatment_count=treatment_count,
        ehr_count=ehr_count,
        consultation_count=consultation_count,
        prescription_count=prescription_count,
        lab_count=lab_count,
        recent_patients=recent_patients,
        recent_appointments=recent_appointments,
        today=date.today()
    )


@app.route("/nurses/delete/<int:id>")
@login_required
def delete_nurse(id):

    nurse = User.query.get_or_404(id)

    db.session.delete(nurse)

    db.session.commit()

    flash("Nurse deleted successfully!", "success")

    return redirect(url_for("nurses"))

@app.route("/nurses/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_nurse(id):

    nurse = User.query.get_or_404(id)

    if request.method == "POST":

        nurse.full_name = request.form["full_name"]
        nurse.username = request.form["username"]
        nurse.email = request.form["email"]
        nurse.phone = request.form["phone"]

        db.session.commit()

        flash("Nurse updated successfully!", "success")

        return redirect(url_for("nurses"))

    return render_template(
        "edit_nurse.html",
        nurse=nurse
    )

#admin

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():

    patient_count = Patient.query.count()
    doctor_count = User.query.filter_by(role="doctor").count()
    nurse_count = User.query.filter_by(role="nurse").count()
    appointment_count = Appointment.query.count()
    treatment_count = Treatment.query.count()
    bill_count = Bill.query.count()
    ehr_count = EHR.query.count()
    consultation_count = Consultation.query.count()
    prescription_count = Prescription.query.count()
    lab_count = LabReport.query.count()

    # Pharmacy Inventory stats
    medicine_count = Medicine.query.count()
    total_stock = db.session.query(db.func.sum(Medicine.quantity)).scalar() or 0

    # Billing Sum stats
    total_billed = db.session.query(db.func.sum(Bill.amount)).scalar() or 0.0
    total_paid = db.session.query(db.func.sum(Bill.amount)).filter_by(payment_status="Paid").scalar() or 0.0
    total_pending = db.session.query(db.func.sum(Bill.amount)).filter_by(payment_status="Pending").scalar() or 0.0

    # Login audit logs
    login_activities = LoginActivity.query.order_by(LoginActivity.id.desc()).limit(15).all()

    recent_patients = Patient.query.order_by(
        Patient.id.desc()
    ).limit(5).all()

    recent_appointments = Appointment.query.order_by(
        Appointment.id.desc()
    ).limit(5).all()

    return render_template(
        "admin_dashboard.html",
        patient_count=patient_count,
        doctor_count=doctor_count,
        nurse_count=nurse_count,
        appointment_count=appointment_count,
        treatment_count=treatment_count,
        bill_count=bill_count,
        ehr_count=ehr_count,
        consultation_count=consultation_count,
        prescription_count=prescription_count,
        lab_count=lab_count,
        medicine_count=medicine_count,
        total_stock=total_stock,
        total_billed=total_billed,
        total_paid=total_paid,
        total_pending=total_pending,
        login_activities=login_activities,
        recent_patients=recent_patients,
        recent_appointments=recent_appointments,
        today=date.today()
    )


# EHR MODULE

@app.route("/ehrs")
@login_required
def ehrs():
    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        ehr_records = EHR.query.filter_by(patient_id=patient.id).all()
    else:
        patient_id = request.args.get('patient_id')
        if patient_id:
            ehr_records = EHR.query.filter_by(patient_id=patient_id).all()
        else:
            ehr_records = EHR.query.all()

    return render_template(
        "ehrs.html",
        ehr_records=ehr_records
    )

@app.route("/ehr/add", methods=["GET", "POST"])
@login_required
def add_ehr():
    if current_user.role.lower() == 'patient':
        flash("Access denied. Patients cannot create EHR records.", "danger")
        return redirect(url_for("ehrs"))

    form = EHRForm()
    form.patient.choices = [(p.id, f"{p.full_name} (ID: {p.id})") for p in Patient.query.all()]

    if form.validate_on_submit():
        ehr = EHR(
            patient_id=form.patient.data,
            doctor_id=current_user.id if current_user.role.lower() == 'doctor' else None,
            medical_history=form.medical_history.data,
            allergies=form.allergies.data,
            current_medications=form.current_medications.data,
            blood_pressure=form.blood_pressure.data,
            heart_rate=form.heart_rate.data,
            temperature=form.temperature.data,
            weight=form.weight.data,
            notes=form.notes.data
        )
        db.session.add(ehr)
        db.session.commit()
        flash("EHR record added successfully!", "success")
        return redirect(url_for("ehrs"))

    return render_template("add_ehr.html", form=form)

@app.route("/ehr/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_ehr(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied. Patients cannot edit EHR records.", "danger")
        return redirect(url_for("ehrs"))

    ehr = EHR.query.get_or_404(id)
    form = EHRForm(obj=ehr)
    form.patient.choices = [(p.id, f"{p.full_name} (ID: {p.id})") for p in Patient.query.all()]

    if request.method == "GET":
        form.patient.data = ehr.patient_id

    if form.validate_on_submit():
        ehr.patient_id = form.patient.data
        if current_user.role.lower() == 'doctor':
            ehr.doctor_id = current_user.id
        ehr.medical_history = form.medical_history.data
        ehr.allergies = form.allergies.data
        ehr.current_medications = form.current_medications.data
        ehr.blood_pressure = form.blood_pressure.data
        ehr.heart_rate = form.heart_rate.data
        ehr.temperature = form.temperature.data
        ehr.weight = form.weight.data
        ehr.notes = form.notes.data

        db.session.commit()
        flash("EHR record updated successfully!", "success")
        return redirect(url_for("ehrs"))

    return render_template("edit_ehr.html", form=form, ehr=ehr)

@app.route("/ehr/view/<int:id>")
@login_required
def view_ehr(id):
    ehr = EHR.query.get_or_404(id)

    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        if ehr.patient_id != patient.id:
            flash("Access denied. You can only view your own EHR records.", "danger")
            return redirect(url_for("ehrs"))

    return render_template("view_ehr.html", ehr=ehr)


# CONSULTATION MODULE

@app.route("/consultations")
@login_required
def consultations():
    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        consultation_list = Consultation.query.filter_by(patient_id=patient.id).order_by(Consultation.consultation_date.desc()).all()
    else:
        patient_id = request.args.get('patient_id')
        if patient_id:
            consultation_list = Consultation.query.filter_by(patient_id=patient_id).order_by(Consultation.consultation_date.desc()).all()
        else:
            consultation_list = Consultation.query.order_by(Consultation.consultation_date.desc()).all()

    return render_template(
        "consultations.html",
        consultations=consultation_list
    )

@app.route("/consultation/add", methods=["GET", "POST"])
@login_required
def add_consultation():
    if current_user.role.lower() == 'patient':
        flash("Access denied. Patients cannot create consultation records.", "danger")
        return redirect(url_for("consultations"))

    form = ConsultationForm()
    form.patient.choices = [(p.id, f"{p.full_name} (ID: {p.id})") for p in Patient.query.all()]

    if request.method == "GET" and not form.consultation_date.data:
        form.consultation_date.data = date.today()

    if form.validate_on_submit():
        fee = form.fee.data
        bill_id = None
        if fee and fee > 0:
            bill = Bill(
                patient_id=form.patient.data,
                amount=float(fee),
                payment_status="Pending",
                bill_date=form.consultation_date.data or date.today()
            )
            db.session.add(bill)
            db.session.flush()
            bill_id = bill.id

        consultation = Consultation(
            patient_id=form.patient.data,
            doctor_id=current_user.id,
            consultation_date=form.consultation_date.data,
            symptoms=form.symptoms.data,
            diagnosis=form.diagnosis.data,
            notes=form.notes.data,
            bill_id=bill_id
        )
        db.session.add(consultation)
        db.session.commit()
        if bill_id:
            trigger_billing_notification(bill)
        flash("Consultation recorded successfully!", "success")
        return redirect(url_for("consultations"))

    return render_template("add_consultation.html", form=form)

@app.route("/consultation/view/<int:id>")
@login_required
def view_consultation(id):
    consultation = Consultation.query.get_or_404(id)

    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        if consultation.patient_id != patient.id:
            flash("Access denied. You can only view your own consultation records.", "danger")
            return redirect(url_for("consultations"))

    return render_template("view_consultation.html", consultation=consultation)


# PRESCRIPTION MODULE

@app.route("/prescriptions")
@login_required
def prescriptions():
    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        prescription_list = Prescription.query.filter_by(patient_id=patient.id).order_by(Prescription.date_prescribed.desc()).all()
    else:
        patient_id = request.args.get('patient_id')
        if patient_id:
            prescription_list = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.date_prescribed.desc()).all()
        else:
            prescription_list = Prescription.query.order_by(Prescription.date_prescribed.desc()).all()

    return render_template(
        "prescriptions.html",
        prescriptions=prescription_list
    )

@app.route("/prescription/add", methods=["GET", "POST"])
@login_required
def add_prescription():
    if current_user.role.lower() == 'patient':
        flash("Access denied. Patients cannot create prescriptions.", "danger")
        return redirect(url_for("prescriptions"))

    form = PrescriptionForm()
    form.patient.choices = [(p.id, f"{p.full_name} (ID: {p.id})") for p in Patient.query.all()]

    if request.method == "GET" and not form.date_prescribed.data:
        form.date_prescribed.data = date.today()

    if form.validate_on_submit():
        prescription = Prescription(
            patient_id=form.patient.data,
            doctor_id=current_user.id,
            medication_name=form.medication_name.data,
            dosage=form.dosage.data,
            frequency=form.frequency.data,
            duration=form.duration.data,
            instructions=form.instructions.data,
            date_prescribed=form.date_prescribed.data
        )
        db.session.add(prescription)
        db.session.commit()

        # Trigger prescription notification
        patient_uid = get_user_id_for_patient(prescription.patient_id)
        msg = f"A new prescription has been created for medication '{prescription.medication_name}'."
        create_notification(patient_uid, "Prescription Created", msg, "Prescription", related_id=prescription.id)

        flash("Prescription added successfully!", "success")
        return redirect(url_for("prescriptions"))

    return render_template("add_prescription.html", form=form)

@app.route("/prescription/view/<int:id>")
@login_required
def view_prescription(id):
    prescription = Prescription.query.get_or_404(id)

    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        if prescription.patient_id != patient.id:
            flash("Access denied. You can only view your own prescriptions.", "danger")
            return redirect(url_for("prescriptions"))

    return render_template("view_prescription.html", prescription=prescription)


# LABORATORY MODULE

@app.route("/lab_reports")
@login_required
def lab_reports():
    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        report_list = LabReport.query.filter_by(patient_id=patient.id).order_by(LabReport.request_date.desc()).all()
    else:
        patient_id = request.args.get('patient_id')
        if patient_id:
            report_list = LabReport.query.filter_by(patient_id=patient_id).order_by(LabReport.request_date.desc()).all()
        else:
            report_list = LabReport.query.order_by(LabReport.request_date.desc()).all()

    return render_template(
        "lab_reports.html",
        lab_reports=report_list
    )

@app.route("/lab_report/request", methods=["GET", "POST"])
@login_required
def request_lab_report():
    if current_user.role.lower() == 'patient':
        flash("Access denied. Patients cannot request lab reports.", "danger")
        return redirect(url_for("lab_reports"))

    form = LabReportRequestForm()
    form.patient.choices = [(p.id, f"{p.full_name} (ID: {p.id})") for p in Patient.query.all()]

    if request.method == "GET" and not form.request_date.data:
        form.request_date.data = date.today()

    if form.validate_on_submit():
        cost = form.test_cost.data
        bill_id = None
        if cost and cost > 0:
            bill = Bill(
                patient_id=form.patient.data,
                amount=float(cost),
                payment_status="Pending",
                bill_date=form.request_date.data or date.today()
            )
            db.session.add(bill)
            db.session.flush()
            bill_id = bill.id

        lab_report = LabReport(
            patient_id=form.patient.data,
            requested_by_id=current_user.id,
            test_name=form.test_name.data,
            request_date=form.request_date.data,
            lab_notes=form.lab_notes.data,
            status="Pending",
            bill_id=bill_id
        )
        db.session.add(lab_report)
        db.session.commit()
        if bill_id:
            trigger_billing_notification(bill)
        flash("Lab report requested successfully!", "success")
        return redirect(url_for("lab_reports"))

    return render_template("request_lab_report.html", form=form)

@app.route("/lab_report/update/<int:id>", methods=["GET", "POST"])
@login_required
def update_lab_report(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied. Patients cannot update lab results.", "danger")
        return redirect(url_for("lab_reports"))

    lab_report = LabReport.query.get_or_404(id)
    form = LabReportResultForm(obj=lab_report)

    if request.method == "GET" and not form.result_date.data:
        form.result_date.data = date.today()

    if form.validate_on_submit():
        lab_report.results = form.results.data
        lab_report.status = form.status.data
        lab_report.result_date = form.result_date.data
        if form.lab_notes.data:
            lab_report.lab_notes = form.lab_notes.data
        lab_report.performed_by_id = current_user.id

        db.session.commit()

        # Trigger lab report completion notification
        if lab_report.status == "Completed":
            patient_uid = get_user_id_for_patient(lab_report.patient_id)
            msg = f"The results for test '{lab_report.test_name}' are now available. Status: Completed."
            create_notification(patient_uid, "Lab Report Available", msg, "Laboratory", related_id=lab_report.id)
            
            # Notify the requesting doctor
            if lab_report.requested_by_id:
                msg_doc = f"Lab results completed for Patient {lab_report.patient.full_name} - test: '{lab_report.test_name}'."
                create_notification(lab_report.requested_by_id, "Lab Report Completed", msg_doc, "Laboratory", related_id=lab_report.id)

        flash("Lab test results updated successfully!", "success")
        return redirect(url_for("lab_reports"))

    return render_template("update_lab_report.html", form=form, lab_report=lab_report)

@app.route("/lab_report/view/<int:id>")
@login_required
def view_lab_report(id):
    lab_report = LabReport.query.get_or_404(id)

    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        if lab_report.patient_id != patient.id:
            flash("Access denied. You can only view your own lab reports.", "danger")
            return redirect(url_for("lab_reports"))

    return render_template("view_lab_report.html", lab_report=lab_report)


# PATIENT MEDICAL HISTORY MODULE

@app.route("/patient/history/<int:id>")
@login_required
def patient_history(id):
    patient = Patient.query.get_or_404(id)

    if current_user.role.lower() == 'patient':
        user_patient = get_patient_for_user(current_user)
        if patient.id != user_patient.id:
            flash("Access denied. You can only view your own medical history.", "danger")
            return redirect(url_for("patient_dashboard"))

    ehrs = EHR.query.filter_by(patient_id=id).all()
    consultations = Consultation.query.filter_by(patient_id=id).all()
    prescriptions = Prescription.query.filter_by(patient_id=id).all()
    lab_reports = LabReport.query.filter_by(patient_id=id).all()
    treatments = Treatment.query.filter_by(patient_id=id).all()
    bills = Bill.query.filter_by(patient_id=id).all()
    dispensings = DispensingRecord.query.filter_by(patient_id=id).all()

    timeline = []

    for item in ehrs:
        timeline.append({
            'type': 'EHR',
            'title': 'Electronic Health Record',
            'date': item.created_at.date() if item.created_at else date.today(),
            'item': item,
            'icon': 'bi-file-earmark-medical',
            'badge': 'bg-info text-dark'
        })

    for item in consultations:
        timeline.append({
            'type': 'Consultation',
            'title': f'Consultation: {item.diagnosis or "Clinical Visit"}',
            'date': item.consultation_date,
            'item': item,
            'icon': 'bi-stethoscope',
            'badge': 'bg-primary'
        })

    for item in prescriptions:
        timeline.append({
            'type': 'Prescription',
            'title': f'Prescription: {item.medication_name}',
            'date': item.date_prescribed,
            'item': item,
            'icon': 'bi-prescription2',
            'badge': 'bg-success'
        })

    for item in lab_reports:
        timeline.append({
            'type': 'Lab Report',
            'title': f'Lab Test: {item.test_name}',
            'date': item.request_date,
            'item': item,
            'icon': 'bi-radioactive',
            'badge': 'bg-warning text-dark'
        })

    for item in treatments:
        timeline.append({
            'type': 'Treatment',
            'title': f'Treatment: {item.diagnosis or item.treatment_details or "Medical Care"}',
            'date': item.date,
            'item': item,
            'icon': 'bi-capsule-pill',
            'badge': 'bg-secondary'
        })

    for item in bills:
        timeline.append({
            'type': 'Bill',
            'title': f'Invoice Billing: ${item.amount}',
            'date': item.bill_date,
            'item': item,
            'icon': 'bi-credit-card',
            'badge': 'bg-danger'
        })

    for item in dispensings:
        timeline.append({
            'type': 'Dispensed',
            'title': f'Medicine Dispensed: {item.medicine.name} × {item.quantity}',
            'date': item.dispensed_date,
            'item': item,
            'icon': 'bi-capsule',
            'badge': 'bg-success text-white'
        })

    # Sort descending by date
    timeline.sort(key=lambda x: x['date'], reverse=True)

    return render_template(
        "patient_history.html",
        patient=patient,
        timeline=timeline,
        ehr_count=len(ehrs),
        consultation_count=len(consultations),
        prescription_count=len(prescriptions),
        lab_count=len(lab_reports),
        treatment_count=len(treatments),
        bill_count=len(bills),
        dispensing_count=len(dispensings)
    )

@app.route("/patient/my-history")
@login_required
def my_history():
    if current_user.role.lower() != 'patient':
        flash("Please select a patient to view medical history.", "warning")
        return redirect(url_for("patients"))

    patient = get_patient_for_user(current_user)
    return redirect(url_for("patient_history", id=patient.id))


# SEARCH & REPORTS MODULE

@app.route("/reports/search")
@login_required
def search_reports():
    if current_user.role.lower() == 'patient':
        flash("Access denied. Patients cannot search other patient records.", "danger")
        return redirect(url_for("patient_dashboard"))

    query = request.args.get("q", "").strip()
    search_by = request.args.get("search_by", "name").strip()

    patients = []
    error_message = None
    is_search_submitted = "search_by" in request.args

    if is_search_submitted:
        if not query:
            error_message = "Search query cannot be empty."
        else:
            if search_by == "id":
                if not query.isdigit():
                    error_message = "Patient ID must be a numeric value."
                else:
                    patient_id = int(query)
                    patients = Patient.query.filter_by(id=patient_id).all()
            elif search_by == "name":
                patients = Patient.query.filter(Patient.full_name.ilike(f"%{query}%")).all()
            elif search_by == "phone":
                patients = Patient.query.filter(Patient.phone.ilike(f"%{query}%")).all()
            elif search_by == "aadhaar":
                patients = Patient.query.filter(Patient.aadhaar.ilike(f"%{query}%")).all()
            elif search_by == "email":
                patients = Patient.query.filter(Patient.email.ilike(f"%{query}%")).all()
            else:
                error_message = "Invalid search criterion."
    else:
        patients = Patient.query.order_by(Patient.id.desc()).limit(20).all()

    if error_message:
        flash(error_message, "danger")

    total_patients = Patient.query.count()
    total_ehrs = EHR.query.count()
    total_consultations = Consultation.query.count()
    total_prescriptions = Prescription.query.count()
    total_labs = LabReport.query.count()
    pending_labs = LabReport.query.filter_by(status="Pending").count()

    return render_template(
        "search_reports.html",
        query=query,
        search_by=search_by,
        patients=patients,
        is_search_submitted=is_search_submitted,
        total_patients=total_patients,
        total_ehrs=total_ehrs,
        total_consultations=total_consultations,
        total_prescriptions=total_prescriptions,
        total_labs=total_labs,
        pending_labs=pending_labs
    )


# ==================================================
# PHARMACY PORTAL ROUTES
# ==================================================

# Helper helper to verify role permissions
def check_pharmacy_access(required_roles=None):
    if not current_user.is_authenticated:
        return redirect(url_for("login", role="admin"))
    if current_user.role.lower() == 'patient':
        flash("Access denied. Patients do not have access to the Pharmacy Management portal.", "danger")
        return redirect(url_for("patient_dashboard"))
    if required_roles and current_user.role.lower() not in required_roles:
        flash(f"Access denied. Only {', '.join(required_roles)} can access this resource.", "danger")
        return redirect(url_for("pharmacy_dashboard"))
    return None

@app.route("/pharmacy")
@login_required
def pharmacy_dashboard():
    access_denied = check_pharmacy_access()
    if access_denied:
        return access_denied

    today_date = date.today()
    total_medicines = Medicine.query.count()
    
    # Stock calculations
    total_stock_units = db.session.query(db.func.sum(Medicine.quantity)).scalar() or 0
    
    # Low stock level (quantity > 0 and quantity < 10)
    low_stock_count = Medicine.query.filter(Medicine.quantity > 0, Medicine.quantity < 10).count()
    
    # Expired level (expiry_date < today)
    expired_count = Medicine.query.filter(Medicine.expiry_date < today_date).count()
    
    # Out of stock level (quantity == 0)
    out_of_stock_count = Medicine.query.filter_by(quantity=0).count()
    
    # Today's dispensing activity
    today_dispensing_count = DispensingRecord.query.filter_by(dispensed_date=today_date).count()

    # Tables for Dashboard
    low_stock_medicines = Medicine.query.filter(Medicine.quantity > 0, Medicine.quantity < 10).limit(5).all()
    expired_medicines = Medicine.query.filter(Medicine.expiry_date < today_date).limit(5).all()
    recent_dispensings = DispensingRecord.query.order_by(DispensingRecord.id.desc()).limit(5).all()

    return render_template(
        "pharmacy_dashboard.html",
        total_medicines=total_medicines,
        total_stock_units=total_stock_units,
        low_stock_count=low_stock_count,
        expired_count=expired_count,
        out_of_stock_count=out_of_stock_count,
        today_dispensing_count=today_dispensing_count,
        low_stock_medicines=low_stock_medicines,
        expired_medicines=expired_medicines,
        recent_dispensings=recent_dispensings
    )

@app.route("/pharmacy/medicines")
@login_required
def pharmacy_medicines():
    access_denied = check_pharmacy_access()
    if access_denied:
        return access_denied

    filter_type = request.args.get("filter", "all")
    today_date = date.today()

    if filter_type == "low_stock":
        medicines = Medicine.query.filter(Medicine.quantity > 0, Medicine.quantity < 10).all()
    elif filter_type == "expired":
        medicines = Medicine.query.filter(Medicine.expiry_date < today_date).all()
    elif filter_type == "out_of_stock":
        medicines = Medicine.query.filter_by(quantity=0).all()
    else:
        medicines = Medicine.query.all()

    return render_template(
        "medicines.html",
        medicines=medicines,
        filter_type=filter_type
    )

@app.route("/pharmacy/medicine/add", methods=["GET", "POST"])
@login_required
def add_medicine():
    access_denied = check_pharmacy_access(required_roles=["admin", "pharmacist"])
    if access_denied:
        return access_denied

    form = MedicineForm()
    if form.validate_on_submit():
        medicine = Medicine(
            name=form.name.data,
            category=form.category.data,
            manufacturer=form.manufacturer.data,
            batch_number=form.batch_number.data,
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            expiry_date=form.expiry_date.data,
            description=form.description.data
        )
        db.session.add(medicine)
        db.session.commit()
        flash("Medicine added to inventory successfully!", "success")
        return redirect(url_for("pharmacy_medicines"))

    return render_template("add_medicine.html", form=form)

@app.route("/pharmacy/medicine/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_medicine(id):
    access_denied = check_pharmacy_access(required_roles=["admin", "pharmacist"])
    if access_denied:
        return access_denied

    medicine = Medicine.query.get_or_404(id)
    form = MedicineForm(obj=medicine)

    if form.validate_on_submit():
        medicine.name = form.name.data
        medicine.category = form.category.data
        medicine.manufacturer = form.manufacturer.data
        medicine.batch_number = form.batch_number.data
        medicine.quantity = form.quantity.data
        medicine.unit_price = form.unit_price.data
        medicine.expiry_date = form.expiry_date.data
        medicine.description = form.description.data
        db.session.commit()
        flash("Medicine updated successfully!", "success")
        return redirect(url_for("pharmacy_medicines"))

    return render_template("edit_medicine.html", form=form, medicine=medicine)

@app.route("/pharmacy/medicine/delete/<int:id>")
@login_required
def delete_medicine(id):
    access_denied = check_pharmacy_access(required_roles=["admin", "pharmacist"])
    if access_denied:
        return access_denied

    medicine = Medicine.query.get_or_404(id)
    if medicine.dispensing_records:
        flash("Cannot delete medicine because dispensing records reference it. Set stock to 0 instead.", "danger")
        return redirect(url_for("pharmacy_medicines"))

    db.session.delete(medicine)
    db.session.commit()
    flash("Medicine deleted from inventory successfully!", "success")
    return redirect(url_for("pharmacy_medicines"))

@app.route("/pharmacy/medicine/update-stock/<int:id>", methods=["GET", "POST"])
@login_required
def update_stock(id):
    access_denied = check_pharmacy_access(required_roles=["admin", "nurse", "pharmacist"])
    if access_denied:
        return access_denied

    medicine = Medicine.query.get_or_404(id)
    form = StockUpdateForm()

    if form.validate_on_submit():
        replenish_qty = form.quantity.data
        medicine.quantity += replenish_qty
        db.session.commit()
        flash(f"Successfully replenished stock level. Added {replenish_qty} units of {medicine.name}.", "success")
        return redirect(url_for("pharmacy_medicines"))

    return render_template("update_stock.html", form=form, medicine=medicine)

@app.route("/pharmacy/dispense", methods=["GET", "POST"])
@login_required
def dispense_medicine():
    access_denied = check_pharmacy_access(required_roles=["admin", "nurse", "pharmacist"])
    if access_denied:
        return access_denied

    form = DispenseForm()
    form.patient.choices = [(p.id, f"{p.full_name} (ID: #{p.id})") for p in Patient.query.all()]
    form.medicine.choices = [(m.id, f"{m.name} (Qty: {m.quantity}, Price: ₹{m.unit_price})") for m in Medicine.query.all()]

    if form.validate_on_submit():
        patient = Patient.query.get(form.patient.data)
        medicine = Medicine.query.get(form.medicine.data)
        qty = form.quantity.data

        if not patient:
            flash("Selected patient does not exist.", "danger")
            return redirect(url_for("dispense_medicine"))
        if not medicine:
            flash("Selected medicine does not exist.", "danger")
            return redirect(url_for("dispense_medicine"))
        
        if qty <= 0:
            flash("Dispensing quantity must be positive.", "danger")
            return redirect(url_for("dispense_medicine"))
            
        if medicine.expiry_date < date.today():
            flash("Cannot dispense medicine. This batch is expired!", "danger")
            return redirect(url_for("dispense_medicine"))

        if medicine.quantity < qty:
            flash(f"Insufficient stock. Requested: {qty}, Available: {medicine.quantity}.", "danger")
            return redirect(url_for("dispense_medicine"))

        try:
            total_amount = Decimal(qty) * medicine.unit_price
            
            bill = Bill(
                patient_id=patient.id,
                amount=float(total_amount),
                payment_status="Pending",
                bill_date=date.today()
            )
            db.session.add(bill)
            db.session.flush()

            medicine.quantity -= qty

            record = DispensingRecord(
                patient_id=patient.id,
                medicine_id=medicine.id,
                quantity=qty,
                unit_price=medicine.unit_price,
                total_amount=total_amount,
                dispensed_by_id=current_user.id,
                dispensed_date=date.today(),
                bill_id=bill.id
            )
            db.session.add(record)
            db.session.commit()
            trigger_billing_notification(bill)
            flash(f"Medicine dispensed successfully! Invoiced amount: ₹{total_amount:.2f}", "success")
            return redirect(url_for("pharmacy_dispensing_history"))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred during dispensing transaction: {str(e)}", "danger")
            return redirect(url_for("dispense_medicine"))

    return render_template("dispense_medicine.html", form=form, medicines=Medicine.query.all())

@app.route("/pharmacy/dispensing-history")
@login_required
def pharmacy_dispensing_history():
    access_denied = check_pharmacy_access(required_roles=["admin", "nurse", "pharmacist"])
    if access_denied:
        return access_denied

    records = DispensingRecord.query.order_by(DispensingRecord.id.desc()).all()
    return render_template("dispensing_history.html", records=records)

@app.context_processor
def inject_date():
    return dict(date=date, today=date.today())


@app.route("/notifications")
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    updated = False
    for n in user_notifications:
        if n.delivery_status == "Pending":
            n.delivery_status = "Delivered"
            updated = True
    if updated:
        db.session.commit()
    return render_template("notifications.html", notifications=user_notifications)


@app.route("/notifications/read/<int:id>", methods=["POST"])
@login_required
def read_notification(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("notifications"))
    notification.status = "Read"
    notification.delivery_status = "Delivered"
    db.session.commit()
    flash("Notification marked as read.", "success")
    return redirect(url_for("notifications"))


@app.route("/notifications/read-all", methods=["POST"])
@login_required
def read_all_notifications():
    unread_notifications = Notification.query.filter_by(user_id=current_user.id).filter(Notification.status != "Read").all()
    for n in unread_notifications:
        n.status = "Read"
        n.delivery_status = "Delivered"
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notifications"))