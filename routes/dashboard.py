from flask import render_template, redirect, url_for, flash, request
from app import app
from extensions import db
from models import Patient, Appointment, Treatment, Bill, User, EHR, Consultation, Prescription, LabReport
from forms import PatientForm, AppointmentForm, TreatmentForm, BillingForm, EHRForm, ConsultationForm, PrescriptionForm, LabReportRequestForm, LabReportResultForm
from flask_login import login_required, current_user
from datetime import date

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

        patient = Patient(

            full_name=form.full_name.data,
            age=form.age.data,
            gender=form.gender.data,
            phone=form.phone.data,
            address=form.address.data,
            blood_group=form.blood_group.data,
            disease=form.disease.data

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

        patient.full_name = form.full_name.data
        patient.age = form.age.data
        patient.gender = form.gender.data
        patient.phone = form.phone.data
        patient.address = form.address.data
        patient.blood_group = form.blood_group.data
        patient.disease = form.disease.data

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

        treatment = Treatment(

            patient_id=form.patient.data,

            diagnosis=form.diagnosis.data,

            medicines=form.medicines.data,

            notes=form.notes.data,

            date=form.date.data

        )

        db.session.add(treatment)

        db.session.commit()

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
@app.route("/bills")
@login_required
def bills():
    if current_user.role.lower() == 'patient':
        patient = get_patient_for_user(current_user)
        bills = Bill.query.filter_by(patient_id=patient.id).all()
    else:
        bills = Bill.query.all()

    return render_template(
        "bills.html",
        bills=bills
    )

@app.route("/bills/add", methods=["GET", "POST"])
@login_required
def add_bill():
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    form = BillingForm()

    form.patient.choices = [
        (p.id, p.full_name)
        for p in Patient.query.all()
    ]

    if form.validate_on_submit():

        bill = Bill(

            patient_id=form.patient.data,

            amount=form.amount.data,

            payment_status=form.payment_status.data,

            bill_date=form.bill_date.data

        )

        db.session.add(bill)

        db.session.commit()

        flash("Bill added successfully!", "success")

        return redirect(url_for("bills"))

    return render_template(
        "add_bill.html",
        form=form
    )

@app.route("/bills/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_bill(id):
    if current_user.role.lower() == 'patient':
        flash("Access denied.", "danger")
        return redirect(url_for("patient_dashboard"))

    bill = Bill.query.get_or_404(id)

    form = BillingForm(obj=bill)

    form.patient.choices = [
        (p.id, p.full_name)
        for p in Patient.query.all()
    ]

    if form.validate_on_submit():

        bill.patient_id = form.patient.data
        bill.amount = form.amount.data
        bill.payment_status = form.payment_status.data
        bill.bill_date = form.bill_date.data

        db.session.commit()

        flash("Bill updated successfully!", "success")

        return redirect(url_for("bills"))

    return render_template(
        "edit_bill.html",
        form=form
    )

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
        consultation = Consultation(
            patient_id=form.patient.data,
            doctor_id=current_user.id,
            consultation_date=form.consultation_date.data,
            symptoms=form.symptoms.data,
            diagnosis=form.diagnosis.data,
            notes=form.notes.data
        )
        db.session.add(consultation)
        db.session.commit()
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
        lab_report = LabReport(
            patient_id=form.patient.data,
            requested_by_id=current_user.id,
            test_name=form.test_name.data,
            request_date=form.request_date.data,
            lab_notes=form.lab_notes.data,
            status="Pending"
        )
        db.session.add(lab_report)
        db.session.commit()
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
        bill_count=len(bills)
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
    query = request.args.get("q", "").strip()

    patients = []

    if query:
        if query.isdigit():
            patient_id = int(query)
            if current_user.role.lower() == 'patient':
                user_patient = get_patient_for_user(current_user)
                if user_patient.id == patient_id:
                    patients = [user_patient]
            else:
                patients = Patient.query.filter((Patient.id == patient_id) | (Patient.full_name.ilike(f"%{query}%"))).all()
        else:
            if current_user.role.lower() == 'patient':
                user_patient = get_patient_for_user(current_user)
                if query.lower() in user_patient.full_name.lower():
                    patients = [user_patient]
            else:
                patients = Patient.query.filter(Patient.full_name.ilike(f"%{query}%")).all()
    else:
        if current_user.role.lower() == 'patient':
            patients = [get_patient_for_user(current_user)]
        else:
            patients = Patient.query.order_by(Patient.id.desc()).limit(20).all()

    total_patients = Patient.query.count()
    total_ehrs = EHR.query.count()
    total_consultations = Consultation.query.count()
    total_prescriptions = Prescription.query.count()
    total_labs = LabReport.query.count()
    pending_labs = LabReport.query.filter_by(status="Pending").count()

    return render_template(
        "search_reports.html",
        query=query,
        patients=patients,
        total_patients=total_patients,
        total_ehrs=total_ehrs,
        total_consultations=total_consultations,
        total_prescriptions=total_prescriptions,
        total_labs=total_labs,
        pending_labs=pending_labs
    )




