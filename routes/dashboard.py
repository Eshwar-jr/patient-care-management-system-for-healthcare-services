from flask import render_template, redirect, url_for, flash, request, jsonify
from app import app
from extensions import db
from models import Patient, Appointment, Treatment, Bill, User, EHR, Consultation, Prescription, LabReport, Medicine, DispensingRecord, Notification, LoginActivity, Feedback
from forms import PatientForm, AppointmentForm, TreatmentForm, BillingForm, EHRForm, ConsultationForm, PrescriptionForm, LabReportRequestForm, LabReportResultForm, MedicineForm, DispenseForm, StockUpdateForm, RecordPaymentForm, FeedbackForm
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from decimal import Decimal

@app.route("/health", methods=["GET"])
def health_check():
    try:
        db.session.execute(db.select(1))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    status_code = 200 if db_status == "connected" else 500
    return jsonify({
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status
    }), status_code

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
        if request.method == "GET":
            patient_id_arg = request.args.get("patient_id")
            if patient_id_arg and patient_id_arg.isdigit():
                form.patient.data = int(patient_id_arg)

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

import time as _time

_ADMIN_STATS_CACHE = {}
_ADMIN_STATS_CACHE_EXPIRY = 0.0

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role.lower() != "admin":
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for("select_role"))

    global _ADMIN_STATS_CACHE, _ADMIN_STATS_CACHE_EXPIRY
    now = _time.time()
    nocache = request.args.get("nocache")

    if not nocache and now < _ADMIN_STATS_CACHE_EXPIRY and _ADMIN_STATS_CACHE:
        stats = _ADMIN_STATS_CACHE
    else:
        patient_count = Patient.query.count()
        doctor_count = User.query.filter(User.role.ilike("doctor")).count()
        nurse_count = User.query.filter(User.role.ilike("nurse")).count()
        appointment_count = Appointment.query.count()
        treatment_count = Treatment.query.count()
        bill_count = Bill.query.count()
        ehr_count = EHR.query.count()
        consultation_count = Consultation.query.count()
        prescription_count = Prescription.query.count()
        lab_count = LabReport.query.count()

        # Required Day 1 metrics
        today_appointments_count = Appointment.query.filter_by(appointment_date=date.today()).count()
        cancelled_appointments_count = Appointment.query.filter_by(status="Cancelled").count()
        pending_labs_count = LabReport.query.filter_by(status="Pending").count()

        # Monthly patient registrations
        monthly_regs = db.session.query(
            db.func.date_format(Patient.created_at, '%Y-%m').label('month'),
            db.func.count(Patient.id)
        ).group_by('month').order_by('month').all()
        patient_months = [r.month for r in monthly_regs]
        patient_counts = [r[1] for r in monthly_regs]

        # Doctor-wise consultation count
        doctor_consultations = db.session.query(
            User.full_name,
            db.func.count(Consultation.id)
        ).join(Consultation, User.id == Consultation.doctor_id)\
         .group_by(User.id, User.full_name).all()
        doctor_names = [d[0] for d in doctor_consultations]
        consultation_counts = [d[1] for d in doctor_consultations]

        # Appointment trends (last 7 days)
        appointment_trends = db.session.query(
            Appointment.appointment_date,
            db.func.count(Appointment.id)
        ).filter(Appointment.appointment_date >= date.today() - timedelta(days=7))\
         .group_by(Appointment.appointment_date)\
         .order_by(Appointment.appointment_date).all()
        
        last_7_days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
        trend_map = {t[0]: t[1] for t in appointment_trends}
        trend_dates = [d.strftime('%Y-%m-%d') for d in last_7_days]
        trend_counts = [trend_map.get(d, 0) for d in last_7_days]

        # Patient demographics (Gender + Age)
        gender_dist = db.session.query(
            Patient.gender,
            db.func.count(Patient.id)
        ).group_by(Patient.gender).all()
        genders = [g[0] or "Unknown" for g in gender_dist]
        gender_counts = [g[1] for g in gender_dist]

        # Scalar query for age buckets (avoids loading full ORM objects)
        ages = db.session.query(Patient.age).filter(Patient.age.isnot(None)).all()
        age_buckets = {"Under 18": 0, "18-35": 0, "36-50": 0, "50+": 0}
        for (a,) in ages:
            if a < 18: age_buckets["Under 18"] += 1
            elif a <= 35: age_buckets["18-35"] += 1
            elif a <= 50: age_buckets["36-50"] += 1
            else: age_buckets["50+"] += 1
        age_labels = list(age_buckets.keys())
        age_values = list(age_buckets.values())

        # Disease Distribution aggregate query
        disease_query = db.session.query(
            db.func.coalesce(db.func.nullif(Patient.disease, ''), 'Not Specified').label('disease'),
            db.func.count(Patient.id)
        ).group_by('disease').order_by(db.func.count(Patient.id).desc()).limit(6).all()
        disease_labels = [d[0] for d in disease_query]
        disease_counts = [d[1] for d in disease_query]

        # Laboratory Test Statistics aggregate query
        lab_status_query = db.session.query(
            LabReport.status,
            db.func.count(LabReport.id)
        ).group_by(LabReport.status).all()
        lab_status_labels = [l[0] or "Unknown" for l in lab_status_query]
        lab_status_counts = [l[1] for l in lab_status_query]

        # Pharmacy Inventory stats
        medicine_count = Medicine.query.count()
        total_stock = db.session.query(db.func.sum(Medicine.quantity)).scalar() or 0

        # Billing Sum stats
        total_billed = db.session.query(db.func.sum(Bill.amount)).scalar() or 0.0
        total_paid = db.session.query(db.func.sum(Bill.amount)).filter_by(payment_status="Paid").scalar() or 0.0
        total_pending = db.session.query(db.func.sum(Bill.amount)).filter_by(payment_status="Pending").scalar() or 0.0

        # Satisfaction Statistics aggregate query
        feedback_count = Feedback.query.count()
        avg_doc_r = float(db.session.query(db.func.avg(Feedback.doctor_rating)).scalar() or 0.0)
        avg_hosp_r = float(db.session.query(db.func.avg(Feedback.hospital_rating)).scalar() or 0.0)
        avg_lab_r = float(db.session.query(db.func.avg(Feedback.lab_rating)).scalar() or 0.0)
        avg_pharm_r = float(db.session.query(db.func.avg(Feedback.pharmacy_rating)).scalar() or 0.0)
        overall_satisfaction = round((avg_doc_r + avg_hosp_r + avg_lab_r + avg_pharm_r) / 4.0, 1) if feedback_count > 0 else 0.0

        stats = {
            "patient_count": patient_count, "doctor_count": doctor_count, "nurse_count": nurse_count,
            "appointment_count": appointment_count, "treatment_count": treatment_count, "bill_count": bill_count,
            "ehr_count": ehr_count, "consultation_count": consultation_count, "prescription_count": prescription_count,
            "lab_count": lab_count, "today_appointments_count": today_appointments_count,
            "cancelled_appointments_count": cancelled_appointments_count, "pending_labs_count": pending_labs_count,
            "patient_months": patient_months, "patient_counts": patient_counts,
            "doctor_names": doctor_names, "consultation_counts": consultation_counts,
            "trend_dates": trend_dates, "trend_counts": trend_counts,
            "genders": genders, "gender_counts": gender_counts,
            "age_labels": age_labels, "age_values": age_values,
            "disease_labels": disease_labels, "disease_counts": disease_counts,
            "lab_status_labels": lab_status_labels, "lab_status_counts": lab_status_counts,
            "medicine_count": medicine_count, "total_stock": total_stock,
            "total_billed": total_billed, "total_paid": total_paid, "total_pending": total_pending,
            "feedback_count": feedback_count, "overall_satisfaction": overall_satisfaction,
            "avg_doc_r": round(avg_doc_r, 1), "avg_hosp_r": round(avg_hosp_r, 1)
        }
        _ADMIN_STATS_CACHE = stats
        _ADMIN_STATS_CACHE_EXPIRY = now + 60.0

    # Recent lists are always fetched real-time
    login_activities = LoginActivity.query.order_by(LoginActivity.id.desc()).limit(15).all()
    recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()
    recent_appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
    recent_feedbacks = Feedback.query.order_by(Feedback.id.desc()).limit(5).all()

    return render_template(
        "admin_dashboard.html",
        patient_count=stats["patient_count"],
        doctor_count=stats["doctor_count"],
        nurse_count=stats["nurse_count"],
        appointment_count=stats["appointment_count"],
        treatment_count=stats["treatment_count"],
        bill_count=stats["bill_count"],
        ehr_count=stats["ehr_count"],
        consultation_count=stats["consultation_count"],
        prescription_count=stats["prescription_count"],
        lab_count=stats["lab_count"],
        today_appointments_count=stats["today_appointments_count"],
        cancelled_appointments_count=stats["cancelled_appointments_count"],
        pending_labs_count=stats["pending_labs_count"],
        patient_months=stats["patient_months"],
        patient_counts=stats["patient_counts"],
        doctor_names=stats["doctor_names"],
        consultation_counts=stats["consultation_counts"],
        trend_dates=stats["trend_dates"],
        trend_counts=stats["trend_counts"],
        genders=stats["genders"],
        gender_counts=stats["gender_counts"],
        age_labels=stats["age_labels"],
        age_values=stats["age_values"],
        disease_labels=stats["disease_labels"],
        disease_counts=stats["disease_counts"],
        lab_status_labels=stats["lab_status_labels"],
        lab_status_counts=stats["lab_status_counts"],
        medicine_count=stats["medicine_count"],
        total_stock=stats["total_stock"],
        total_billed=stats["total_billed"],
        total_paid=stats["total_paid"],
        total_pending=stats["total_pending"],
        feedback_count=stats["feedback_count"],
        overall_satisfaction=stats["overall_satisfaction"],
        avg_doc_r=stats["avg_doc_r"],
        avg_hosp_r=stats["avg_hosp_r"],
        login_activities=login_activities,
        recent_patients=recent_patients,
        recent_appointments=recent_appointments,
        recent_feedbacks=recent_feedbacks,
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

    if request.method == "GET":
        patient_id_arg = request.args.get("patient_id")
        if patient_id_arg and patient_id_arg.isdigit():
            form.patient.data = int(patient_id_arg)

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

    if request.method == "GET":
        if not form.consultation_date.data:
            form.consultation_date.data = date.today()
        patient_id_arg = request.args.get("patient_id")
        if patient_id_arg and patient_id_arg.isdigit():
            form.patient.data = int(patient_id_arg)

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

        # Update appointment status if appointment_id is present
        appt_id_arg = request.args.get("appointment_id")
        if appt_id_arg and appt_id_arg.isdigit():
            appt = Appointment.query.get(int(appt_id_arg))
            if appt:
                appt.status = "Completed"
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

    if request.method == "GET":
        if not form.date_prescribed.data:
            form.date_prescribed.data = date.today()
        patient_id_arg = request.args.get("patient_id")
        if patient_id_arg and patient_id_arg.isdigit():
            form.patient.data = int(patient_id_arg)

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

    if request.method == "GET":
        if not form.request_date.data:
            form.request_date.data = date.today()
        patient_id_arg = request.args.get("patient_id")
        if patient_id_arg and patient_id_arg.isdigit():
            form.patient.data = int(patient_id_arg)

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


# ==================================================
# PATIENT FEEDBACK & SATISFACTION MODULE
# ==================================================

@app.route("/feedback/add", methods=["GET", "POST"])
@login_required
def add_feedback():
    if current_user.role.lower() != "patient":
        flash("Access denied. Patient feedback submission only.", "danger")
        return redirect(url_for("home"))

    patient = get_patient_for_user(current_user)
    form = FeedbackForm()

    # Get patient's completed consultations
    patient_consultations = Consultation.query.filter_by(patient_id=patient.id).order_by(Consultation.consultation_date.desc()).all()

    if not patient_consultations:
        flash("No completed consultations found. Feedback requires a completed consultation visit.", "warning")
        return redirect(url_for("consultations"))

    form.consultation.choices = [(c.id, f"Consultation #{c.id} - {c.consultation_date} ({c.doctor.full_name if c.doctor else 'Doctor'})") for c in patient_consultations]

    # Pre-select consultation if provided in query string
    pre_consult_id = request.args.get("consultation_id")
    if request.method == "GET" and pre_consult_id:
        try:
            cid = int(pre_consult_id)
            if any(c.id == cid for c in patient_consultations):
                form.consultation.data = cid
        except ValueError:
            pass

    if form.validate_on_submit():
        selected_consultation = Consultation.query.get(form.consultation.data)
        
        # CRITICAL SECURITY RULE: Verify consultation belongs to logged-in patient
        if not selected_consultation or selected_consultation.patient_id != patient.id:
            flash("Access denied. The selected consultation does not belong to your account.", "danger")
            return redirect(url_for("add_feedback"))

        feedback = Feedback(
            patient_id=patient.id,
            doctor_id=selected_consultation.doctor_id,
            consultation_id=selected_consultation.id,
            doctor_rating=form.doctor_rating.data,
            hospital_rating=form.hospital_rating.data,
            lab_rating=form.lab_rating.data,
            pharmacy_rating=form.pharmacy_rating.data,
            comments=form.comments.data
        )

        db.session.add(feedback)
        db.session.commit()

        flash("Thank you! Your feedback has been submitted successfully.", "success")
        return redirect(url_for("feedbacks"))

    return render_template("add_feedback.html", form=form, patient=patient)


@app.route("/feedback")
@login_required
def feedbacks():
    role = current_user.role.lower()

    if role == "patient":
        patient = get_patient_for_user(current_user)
        feedback_list = Feedback.query.filter_by(patient_id=patient.id).order_by(Feedback.created_at.desc()).all()
        doctors = []
        stats = None
    elif role in ["admin", "doctor"]:
        query = Feedback.query.join(Patient)

        # Filters
        doctor_id = request.args.get("doctor_id", "").strip()
        department = request.args.get("department", "").strip()
        start_date_str = request.args.get("start_date", "").strip()
        end_date_str = request.args.get("end_date", "").strip()
        min_rating_str = request.args.get("min_rating", "").strip()

        if doctor_id:
            try:
                query = query.filter(Feedback.doctor_id == int(doctor_id))
            except ValueError:
                pass

        if department:
            # Re-use get_doctor_department mapping
            dept_doctor_ids = [d.id for d in User.query.filter(User.role.ilike("doctor")).all() if get_doctor_department(d.full_name).lower() == department.lower()]
            query = query.filter(Feedback.doctor_id.in_(dept_doctor_ids))

        if start_date_str:
            try:
                s_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                query = query.filter(Feedback.created_at >= s_date)
            except ValueError:
                pass

        if end_date_str:
            try:
                e_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(Feedback.created_at < e_date)
            except ValueError:
                pass

        if min_rating_str:
            try:
                m_rating = float(min_rating_str)
                query = query.filter(Feedback.doctor_rating >= m_rating)
            except ValueError:
                pass

        feedback_list = query.order_by(Feedback.created_at.desc()).all()

        # Doctors list for filter dropdown
        doctors = User.query.filter(User.role.ilike("doctor")).all()

        # Satisfaction Statistics using db.func.avg
        avg_doc = float(db.session.query(db.func.avg(Feedback.doctor_rating)).scalar() or 0.0)
        avg_hosp = float(db.session.query(db.func.avg(Feedback.hospital_rating)).scalar() or 0.0)
        avg_lab = float(db.session.query(db.func.avg(Feedback.lab_rating)).scalar() or 0.0)
        avg_pharm = float(db.session.query(db.func.avg(Feedback.pharmacy_rating)).scalar() or 0.0)
        total_count = Feedback.query.count()
        overall_score = round((avg_doc + avg_hosp + avg_lab + avg_pharm) / 4.0, 1) if total_count > 0 else 0.0

        stats = {
            "avg_doctor": round(avg_doc, 1),
            "avg_hospital": round(avg_hosp, 1),
            "avg_lab": round(avg_lab, 1),
            "avg_pharmacy": round(avg_pharm, 1),
            "overall_score": overall_score,
            "total_count": total_count
        }
    else:
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    return render_template(
        "feedbacks.html",
        feedbacks=feedback_list,
        doctors=doctors,
        stats=stats,
        doctor_departments=DOCTOR_DEPARTMENTS,
        get_doctor_department=get_doctor_department
    )


@app.route("/feedback/view/<int:id>")
@login_required
def view_feedback(id):
    feedback = Feedback.query.get_or_404(id)
    role = current_user.role.lower()

    if role == "patient":
        patient = get_patient_for_user(current_user)
        if feedback.patient_id != patient.id:
            flash("Access denied. You can only view your own feedback records.", "danger")
            return redirect(url_for("feedbacks"))
    elif role not in ["admin", "doctor"]:
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    doctor_dept = get_doctor_department(feedback.doctor.full_name) if feedback.doctor else "General Medicine"

    return render_template("view_feedback.html", feedback=feedback, doctor_dept=doctor_dept)


# ==================================================
# ADMINISTRATIVE REPORTING MODULE
# ==================================================

DOCTOR_DEPARTMENTS = {
    "Dr. Dev": "Cardiology",
    "Dr. Njrr": "Pediatrics",
    "Dr. Smith": "General Medicine",
}

def get_doctor_department(doctor_name):
    if not doctor_name:
        return "General Medicine"
    for name, dept in DOCTOR_DEPARTMENTS.items():
        if name.lower() in doctor_name.lower():
            return dept
    return "General Medicine"

@app.route("/admin/reports")
@login_required
def reports_dashboard():
    if current_user.role.lower() not in ["admin", "doctor"]:
        flash("Access denied. You do not have permission to view administrative reports.", "danger")
        return redirect(url_for("select_role"))
        
    return render_template("reports_dashboard.html")

def get_report_data(report_type, start_date_str, end_date_str, extra_filters):
    """Internal helper to aggregate report data."""
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    headers = []
    rows = []
    
    if report_type == "patients":
        q = Patient.query
        gender = extra_filters.get("gender")
        if start_date:
            q = q.filter(Patient.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            q = q.filter(Patient.created_at <= datetime.combine(end_date, datetime.max.time()))
        if gender:
            q = q.filter(Patient.gender == gender)
        records = q.all()
        headers = ["Patient ID", "Full Name", "Age", "Gender", "Phone Number", "Aadhaar Number", "Email Address", "Registration Date"]
        rows = [[
            p.id, 
            p.full_name, 
            p.age if p.age is not None else 'N/A', 
            p.gender or 'N/A', 
            p.phone or 'N/A', 
            p.aadhaar or 'N/A', 
            p.email or 'N/A', 
            p.created_at.strftime('%Y-%m-%d %I:%M %p') if p.created_at else 'N/A'
        ] for p in records]
        
    elif report_type == "appointments":
        q = Appointment.query
        status = extra_filters.get("status")
        if start_date:
            q = q.filter(Appointment.appointment_date >= start_date)
        if end_date:
            q = q.filter(Appointment.appointment_date <= end_date)
        if status:
            q = q.filter(Appointment.status == status)
        records = q.all()
        headers = ["Appointment ID", "Patient Name", "Doctor Name", "Appointment Date", "Appointment Time", "Reason", "Status"]
        rows = [[
            a.id, 
            a.patient.full_name if a.patient else 'Unknown', 
            a.doctor_name, 
            a.appointment_date.strftime('%Y-%m-%d') if a.appointment_date else 'N/A', 
            a.appointment_time.strftime('%H:%M') if a.appointment_time else 'N/A', 
            a.reason or 'N/A', 
            a.status
        ] for a in records]
        
    elif report_type == "consultations":
        q = Consultation.query
        doc_id = extra_filters.get("doctor_id")
        if start_date:
            q = q.filter(Consultation.consultation_date >= start_date)
        if end_date:
            q = q.filter(Consultation.consultation_date <= end_date)
        if doc_id:
            q = q.filter(Consultation.doctor_id == int(doc_id))
        records = q.all()
        headers = ["Consultation ID", "Patient Name", "Doctor Name", "Consultation Date", "Symptoms", "Diagnosis", "Notes", "Billed Fee (INR)"]
        rows = [[
            c.id, 
            c.patient.full_name if c.patient else 'Unknown', 
            c.doctor.full_name if c.doctor else 'Unknown', 
            c.consultation_date.strftime('%Y-%m-%d') if c.consultation_date else 'N/A', 
            c.symptoms or 'N/A', 
            c.diagnosis or 'N/A', 
            c.notes or 'N/A', 
            f"INR {c.bill.amount:.2f}" if c.bill else '0.00'
        ] for c in records]
        
    elif report_type == "prescriptions":
        q = Prescription.query
        med = extra_filters.get("medication")
        if start_date:
            q = q.filter(Prescription.date_prescribed >= start_date)
        if end_date:
            q = q.filter(Prescription.date_prescribed <= end_date)
        if med:
            q = q.filter(Prescription.medication_name.ilike(f"%{med}%"))
        records = q.all()
        headers = ["Prescription ID", "Patient Name", "Doctor Name", "Medication Name", "Dosage", "Frequency", "Duration", "Date Prescribed"]
        rows = [[
            p.id, 
            p.patient.full_name if p.patient else 'Unknown', 
            p.doctor.full_name if p.doctor else 'Unknown', 
            p.medication_name, 
            p.dosage, 
            p.frequency, 
            p.duration, 
            p.date_prescribed.strftime('%Y-%m-%d') if p.date_prescribed else 'N/A'
        ] for p in records]
        
    elif report_type == "doctors":
        headers = ["Doctor Name", "Total Appointments", "Completed Appointments", "Cancelled Appointments", "Total Consultations", "Prescriptions Prescribed", "Billed Revenue (INR)"]
        doctors = User.query.filter(User.role.ilike("doctor")).all()
        for d in doctors:
            appts_q = Appointment.query.filter(Appointment.doctor_name.ilike(f"%{d.full_name}%"))
            consults_q = Consultation.query.filter_by(doctor_id=d.id)
            prescripts_q = Prescription.query.filter_by(doctor_id=d.id)
            
            if start_date:
                appts_q = appts_q.filter(Appointment.appointment_date >= start_date)
                consults_q = consults_q.filter(Consultation.consultation_date >= start_date)
                prescripts_q = prescripts_q.filter(Prescription.date_prescribed >= start_date)
            if end_date:
                appts_q = appts_q.filter(Appointment.appointment_date <= end_date)
                consults_q = consults_q.filter(Consultation.consultation_date <= end_date)
                prescripts_q = prescripts_q.filter(Prescription.date_prescribed <= end_date)
                
            total_appts = appts_q.count()
            completed_appts = appts_q.filter_by(status="Completed").count()
            cancelled_appts = appts_q.filter_by(status="Cancelled").count()
            total_consults = consults_q.count()
            total_prescripts = prescripts_q.count()
            
            billed_rev = 0.0
            for c in consults_q.all():
                if c.bill:
                    billed_rev += float(c.bill.amount)
                    
            rows.append([
                d.full_name,
                total_appts,
                completed_appts,
                cancelled_appts,
                total_consults,
                total_prescripts,
                f"INR {billed_rev:.2f}"
            ])
            
    elif report_type == "departments":
        depts = ["Cardiology", "Pediatrics", "General Medicine"]
        headers = ["Department Name", "Total Appointments", "Completed Appointments", "Total Consultations", "Billed Revenue (INR)"]
        
        dept_data = {dept: {"total_appts": 0, "completed_appts": 0, "consults": 0, "revenue": 0.0} for dept in depts}
        doctors = User.query.filter(User.role.ilike("doctor")).all()
        doc_dept_map = {d.id: get_doctor_department(d.full_name) for d in doctors}
        doc_name_dept_map = {d.full_name.lower(): get_doctor_department(d.full_name) for d in doctors}
        
        appts_q = Appointment.query
        if start_date:
            appts_q = appts_q.filter(Appointment.appointment_date >= start_date)
        if end_date:
            appts_q = appts_q.filter(Appointment.appointment_date <= end_date)
            
        for a in appts_q.all():
            dept = "General Medicine"
            if a.doctor_name:
                for name_key, d_dept in doc_name_dept_map.items():
                    if name_key in a.doctor_name.lower():
                        dept = d_dept
                        break
            if dept not in dept_data:
                dept_data[dept] = {"total_appts": 0, "completed_appts": 0, "consults": 0, "revenue": 0.0}
            dept_data[dept]["total_appts"] += 1
            if a.status == "Completed":
                dept_data[dept]["completed_appts"] += 1
                
        consults_q = Consultation.query
        if start_date:
            consults_q = consults_q.filter(Consultation.consultation_date >= start_date)
        if end_date:
            consults_q = consults_q.filter(Consultation.consultation_date <= end_date)
            
        for c in consults_q.all():
            dept = doc_dept_map.get(c.doctor_id, "General Medicine")
            if dept not in dept_data:
                dept_data[dept] = {"total_appts": 0, "completed_appts": 0, "consults": 0, "revenue": 0.0}
            dept_data[dept]["consults"] += 1
            if c.bill:
                dept_data[dept]["revenue"] += float(c.bill.amount)
                
        for dept, stats in dept_data.items():
            rows.append([
                dept,
                stats["total_appts"],
                stats["completed_appts"],
                stats["consults"],
                f"INR {stats['revenue']:.2f}"
            ])
            
    elif report_type == "monthly":
        headers = ["Month", "Patient Registrations", "Appointments Booked", "Consultations Handled", "Billed Revenue (INR)"]
        monthly_data = {}
        
        patients_q = Patient.query
        if start_date:
            patients_q = patients_q.filter(Patient.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            patients_q = patients_q.filter(Patient.created_at <= datetime.combine(end_date, datetime.max.time()))
        for p in patients_q.all():
            if p.created_at:
                m_key = p.created_at.strftime('%Y-%m')
                if m_key not in monthly_data:
                    monthly_data[m_key] = {"regs": 0, "appts": 0, "consults": 0, "revenue": 0.0}
                monthly_data[m_key]["regs"] += 1
                
        appts_q = Appointment.query
        if start_date:
            appts_q = appts_q.filter(Appointment.appointment_date >= start_date)
        if end_date:
            appts_q = appts_q.filter(Appointment.appointment_date <= end_date)
        for a in appts_q.all():
            if a.appointment_date:
                m_key = a.appointment_date.strftime('%Y-%m')
                if m_key not in monthly_data:
                    monthly_data[m_key] = {"regs": 0, "appts": 0, "consults": 0, "revenue": 0.0}
                monthly_data[m_key]["appts"] += 1
                
        consults_q = Consultation.query
        if start_date:
            consults_q = consults_q.filter(Consultation.consultation_date >= start_date)
        if end_date:
            consults_q = consults_q.filter(Consultation.consultation_date <= end_date)
        for c in consults_q.all():
            if c.consultation_date:
                m_key = c.consultation_date.strftime('%Y-%m')
                if m_key not in monthly_data:
                    monthly_data[m_key] = {"regs": 0, "appts": 0, "consults": 0, "revenue": 0.0}
                monthly_data[m_key]["consults"] += 1
                if c.bill:
                    monthly_data[m_key]["revenue"] += float(c.bill.amount)
                    
        sorted_months = sorted(list(monthly_data.keys()), reverse=True)
        sorted_months = sorted(list(monthly_data.keys()), reverse=True)
        for m in sorted_months:
            stats = monthly_data[m]
            rows.append([
                m,
                stats["regs"],
                stats["appts"],
                stats["consults"],
                f"INR {stats['revenue']:.2f}"
            ])

    elif report_type == "feedback":
        headers = ["Date", "Patient Name", "Doctor Name", "Department", "Doctor Rating", "Hospital Rating", "Lab Rating", "Pharmacy Rating", "Overall Score", "Comments"]
        fb_q = Feedback.query
        if start_date:
            fb_q = fb_q.filter(Feedback.created_at >= start_date)
        if end_date:
            fb_q = fb_q.filter(Feedback.created_at <= end_date + timedelta(days=1))
        if extra_filters.get("doctor_id"):
            try:
                fb_q = fb_q.filter(Feedback.doctor_id == int(extra_filters["doctor_id"]))
            except ValueError:
                pass
        for f in fb_q.order_by(Feedback.created_at.desc()).all():
            doc_name = f.doctor.full_name if f.doctor else "N/A"
            dept = get_doctor_department(doc_name)
            rows.append([
                f.created_at.strftime('%Y-%m-%d %I:%M %p') if f.created_at else "",
                f.patient.full_name if f.patient else "N/A",
                doc_name,
                dept,
                f"{f.doctor_rating} Stars",
                f"{f.hospital_rating} Stars",
                f"{f.lab_rating} Stars",
                f"{f.pharmacy_rating} Stars",
                f"{f.overall_rating} / 5.0",
                f.comments or "No comments"
            ])
            
    return headers, rows

@app.route("/admin/reports/<report_type>")
@login_required
def view_report(report_type):
    if current_user.role.lower() not in ["admin", "doctor"]:
        flash("Access denied.", "danger")
        return redirect(url_for("select_role"))
        
    valid_reports = ["patients", "appointments", "consultations", "prescriptions", "doctors", "departments", "monthly", "feedback"]
    if report_type not in valid_reports:
        flash("Invalid report type requested.", "danger")
        return redirect(url_for("reports_dashboard"))
        
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()
    
    extra_filters = {
        "gender": request.args.get("gender", "").strip(),
        "status": request.args.get("status", "").strip(),
        "doctor_id": request.args.get("doctor_id", "").strip(),
        "medication": request.args.get("medication", "").strip()
    }
    
    doctors = User.query.filter(User.role.ilike("doctor")).all()
    headers, rows = get_report_data(report_type, start_date_str, end_date_str, extra_filters)
    
    titles = {
        "patients": "Patient Registrations Report",
        "appointments": "Appointment Scheduling Report",
        "consultations": "Doctor Consultations Report",
        "prescriptions": "Prescription Analytics Report",
        "doctors": "Doctor Performance & Activity Report",
        "departments": "Department-wise Activity & Revenue Report",
        "monthly": "Monthly Hospital Aggregations Summary",
        "feedback": "Patient Feedback & Satisfaction Report"
    }
    
    return render_template(
        "view_report.html",
        report_type=report_type,
        report_title=titles[report_type],
        headers=headers,
        rows=rows,
        start_date=start_date_str,
        end_date=end_date_str,
        extra_filters=extra_filters,
        doctors=doctors
    )

@app.route("/admin/reports/export/<report_type>/<export_format>")
@login_required
def export_report(report_type, export_format):
    if current_user.role.lower() not in ["admin", "doctor"]:
        flash("Access denied.", "danger")
        return redirect(url_for("select_role"))
        
    valid_reports = ["patients", "appointments", "consultations", "prescriptions", "doctors", "departments", "monthly", "feedback"]
    valid_formats = ["csv", "excel", "pdf"]
    if report_type not in valid_reports or export_format not in valid_formats:
        flash("Invalid export parameters.", "danger")
        return redirect(url_for("reports_dashboard"))
        
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()
    
    extra_filters = {
        "gender": request.args.get("gender", "").strip(),
        "status": request.args.get("status", "").strip(),
        "doctor_id": request.args.get("doctor_id", "").strip(),
        "medication": request.args.get("medication", "").strip()
    }
    
    headers, rows = get_report_data(report_type, start_date_str, end_date_str, extra_filters)
    
    titles = {
        "patients": "Patient Registrations Report",
        "appointments": "Appointment Scheduling Report",
        "consultations": "Doctor Consultations Report",
        "prescriptions": "Prescription Analytics Report",
        "doctors": "Doctor Performance Report",
        "departments": "Department-wise Activity Report",
        "monthly": "Monthly Hospital Aggregations Summary",
        "feedback": "Patient Feedback & Satisfaction Report"
    }
    
    title = titles[report_type]
    filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    from reports.export_helpers import generate_csv_response, generate_excel_response, generate_pdf_response
    
    if export_format == "csv":
        return generate_csv_response(f"{filename}.csv", headers, rows)
    elif export_format == "excel":
        return generate_excel_response(f"{filename}.xlsx", title, headers, rows)
    elif export_format == "pdf":
        filters_applied = {"Start Date": start_date_str, "End Date": end_date_str}
        filters_applied.update({k.capitalize(): v for k, v in extra_filters.items() if v})
        return generate_pdf_response(f"{filename}.pdf", title, headers, rows, filters_applied)