from flask import render_template, redirect, url_for, flash, request
from app import app
from extensions import db
from models import Patient
from forms import PatientForm
from flask_login import login_required

@app.route("/admin")
@login_required
def admin_dashboard():
    return "<h2>Admin Dashboard</h2>"


@app.route("/doctor")
@login_required
def doctor_dashboard():

    total_patients = Patient.query.count()

    return render_template(
        "doctor_dashboard.html",
        total_patients=total_patients
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

@app.route("/nurse")
@login_required
def nurse_dashboard():
    return "<h2>Nurse Dashboard</h2>"


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