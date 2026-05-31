from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from auth.models import User
from database.db import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    first_user = User.query.count() == 0

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists", "error")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        role = "admin" if first_user else "viewer"

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully", "success")

        return redirect(url_for("auth.login"))

    return render_template(
        "register.html",
        is_first_user=first_user
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            flash("Login successful", "success")

            return redirect(url_for("dashboard.dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully", "success")

    return redirect(url_for("auth.login"))