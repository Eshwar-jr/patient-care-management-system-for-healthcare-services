from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegistrationForm, LoginForm
from models import User, LoginActivity
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


@app.route("/login", defaults={"role": "default"}, methods=["GET", "POST"])
@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if request.path == "/login":
        return redirect(url_for("select_role"))
    role = role.lower()
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            if user.role.lower() != role:
                activity = LoginActivity(
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    role=user.role,
                    ip_address=request.remote_addr,
                    status="Failed",
                    action="Login"
                )
                db.session.add(activity)
                db.session.commit()

                flash("You selected the wrong login portal.", "danger")
                return redirect(url_for("login", role=role))

            activity = LoginActivity(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                ip_address=request.remote_addr,
                status="Success",
                action="Login"
            )
            db.session.add(activity)
            db.session.commit()

            login_user(user, remember=form.remember.data)
            flash("Login Successful!", "success")

            if role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif role == "doctor":
                return redirect(url_for("doctor_dashboard"))
            elif role == "nurse":
                return redirect(url_for("nurse_dashboard"))
            elif role == "patient":
                return redirect(url_for("patient_dashboard"))
            elif role == "pharmacist":
                return redirect(url_for("pharmacy_dashboard"))

        else:
            activity = LoginActivity(
                user_id=user.id if user else None,
                username=form.email.data,
                email=form.email.data,
                role=role,
                ip_address=request.remote_addr,
                status="Failed",
                action="Login"
            )
            db.session.add(activity)
            db.session.commit()

            flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form, role=role)


@app.route("/logout")
@login_required
def logout():
    if current_user.is_authenticated:
        activity = LoginActivity(
            user_id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            role=current_user.role,
            ip_address=request.remote_addr,
            status="Success",
            action="Logout"
        )
        db.session.add(activity)
        db.session.commit()

    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("select_role"))