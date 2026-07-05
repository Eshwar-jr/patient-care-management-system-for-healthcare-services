from flask import render_template, redirect, url_for, flash
from app import app
from flask_login import login_required

@app.route("/admin")
@login_required
def admin_dashboard():
    return "<h2>Admin Dashboard</h2>"


@app.route("/doctor")
@login_required
def doctor_dashboard():
    return render_template(
    "doctor_dashboard.html"
)


@app.route("/nurse")
@login_required
def nurse_dashboard():
    return "<h2>Nurse Dashboard</h2>"


@app.route("/patient")
@login_required
def patient_dashboard():
    return "<h2>Patient Dashboard</h2>"