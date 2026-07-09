from flask import render_template, redirect, url_for, flash, request
from app import app
from extensions import db
from models import Patient, Appointment, Treatment, Bill, User
from forms import PatientForm, AppointmentForm, TreatmentForm, BillingForm
from flask_login import login_required
from datetime import date


from datetime import date

@app.route("/doctor")
@login_required
def doctor_dashboard():

    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()
    treatment_count = Treatment.query.count()
    bill_count = Bill.query.count()

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
           bill_count
    ]

    return render_template(
    "doctor_dashboard.html",
    patient_count=patient_count,
    appointment_count=appointment_count,
    treatment_count=treatment_count,
    bill_count=bill_count,
    recent_patients=recent_patients,
    recent_appointments=recent_appointments,
    today=date.today(),
    chart_data=chart_data
)

@app.route("/patient/add", methods=["GET", "POST"])
@login_required
def add_patient():

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

    patient = Patient.query.get_or_404(id)

    db.session.delete(patient)
    db.session.commit()

    flash("Patient deleted successfully!", "success")

    return redirect(url_for("patients"))


@app.route("/patient/<int:id>")
@login_required
def patient_profile(id):

    patient = Patient.query.get_or_404(id)

    return render_template(
        "patient_profile.html",
        patient=patient
    )


@app.route("/patient")
@login_required
def patient_dashboard():
    return "<h2>Patient Dashboard</h2>"

@app.route("/patients")
@login_required
def patients():

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

    #dropdown

    patients = Patient.query.all()

    print("=" * 50)
    print("Patients found:", len(patients))

    form.patient.choices = []

    for p in patients:
       print(f"ID: {p.id}, Name: {p.full_name}")
       form.patient.choices.append((p.id, p.full_name))

    print("Dropdown choices:", form.patient.choices)
    print("=" * 50)

    if form.validate_on_submit():

        appointment = Appointment(

            patient_id=form.patient.data,

            doctor_name=form.doctor_name.data,

            appointment_date=form.appointment_date.data,

            appointment_time=form.appointment_time.data,

            reason=form.reason.data

        )

        db.session.add(appointment)

        db.session.commit()

        flash("Appointment booked successfully!", "success")

        return redirect(url_for("appointments"))

    return render_template(
        "add_appointment.html",
        form=form
    )

@app.route("/appointments")
@login_required
def appointments():

    appointments = Appointment.query.all()

    return render_template(
        "appointments.html",
        appointments=appointments
    )

@app.route("/appointments/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_appointment(id):

    appointment = Appointment.query.get_or_404(id)

    form = AppointmentForm(obj=appointment)

    form.patient.choices = [
        (p.id, p.full_name)
        for p in Patient.query.all()
    ]

    if form.validate_on_submit():

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

    appointment = Appointment.query.get_or_404(id)

    db.session.delete(appointment)

    db.session.commit()

    flash("Appointment deleted successfully!", "success")

    return redirect(url_for("appointments"))

#TREATMENTS

@app.route("/treatments")
@login_required
def treatments():

    treatments = Treatment.query.all()

    return render_template(
        "treatments.html",
        treatments=treatments
    )

@app.route("/treatments/add", methods=["GET", "POST"])
@login_required
def add_treatment():

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

    treatment = Treatment.query.get_or_404(id)

    db.session.delete(treatment)

    db.session.commit()

    flash("Treatment deleted successfully!", "success")

    return redirect(url_for("treatments"))

#BILLING
@app.route("/bills")
@login_required
def bills():

    bills = Bill.query.all()

    return render_template(
        "bills.html",
        bills=bills
    )

@app.route("/bills/add", methods=["GET", "POST"])
@login_required
def add_bill():

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

        recent_patients=recent_patients,

        recent_appointments=recent_appointments,

        today=date.today()

    )