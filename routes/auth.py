from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegistrationForm, LoginForm
from models import User
from extensions import db
from app import app


@app.route("/")
def home():
    return render_template("home.html")
@app.route("/select-role")
def select_role():
    return render_template("select_role.html")
@app.route("/register", methods=["GET", "POST"])
def register():

    form = RegistrationForm()

    if form.validate_on_submit():

        existing_user = User.query.filter_by(
            username=form.username.data
        ).first()

        if existing_user:

            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        existing_email = User.query.filter_by(
            email=form.email.data
        ).first()

        if existing_email:

            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(
            form.password.data
        )

        user = User(

            full_name=form.full_name.data,

            username=form.username.data,

            email=form.email.data,

            phone=form.phone.data,

            password=hashed_password,

            role=form.role.data

        )

        db.session.add(user)

        db.session.commit()

        flash("Registration Successful!", "success")

        return redirect(url_for("register"))

    return render_template(
        "register.html",
        form=form
    )


@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):

    role = role.lower()

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(
            email=form.email.data
        ).first()

        if user and check_password_hash(
            user.password,
            form.password.data
        ):

            if user.role.lower() != role:

                flash(
                    "You selected the wrong login portal.",
                    "danger"
                )

                return redirect(
                    url_for("login", role=role)
                )

            login_user(
                user,
                remember=form.remember.data
            )

            flash(
                "Login Successful!",
                "success"
            )

            if role == "admin":
                return redirect(
                    url_for("admin_dashboard")
                )

            elif role == "doctor":
                return redirect(
                    url_for("doctor_dashboard")
                )

            elif role == "nurse":
                return redirect(
                    url_for("nurse_dashboard")
                )
            elif role == "patient":
                return redirect(
                    url_for("patient_dashboard")
            )

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template(
        "login.html",
        form=form,
        role=role
    )
@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("select_role"))