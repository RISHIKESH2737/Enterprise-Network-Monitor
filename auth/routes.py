from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError

from auth.models import User
from database.db import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    first_user = User.query.count() == 0

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validate required fields
        if not username or not email or not password or not confirm_password:
            flash("All fields are required.", "error")
            return redirect(url_for("auth.register"))

        # Password validation
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))

        # Check username
        existing_username = User.query.filter_by(username=username).first()

        if existing_username:
            flash("Username already exists.", "error")
            return redirect(url_for("auth.register"))

        # Check email
        existing_email = User.query.filter_by(email=email).first()

        if existing_email:
            flash("Email already registered. Please login.", "error")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        role = "admin" if first_user else "viewer"

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            role=role
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            flash("Account created successfully.", "success")
            return redirect(url_for("auth.login"))

        except IntegrityError:
            db.session.rollback()
            flash("Username or Email already exists.", "error")
            return redirect(url_for("auth.register"))

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {e}", "error")
            return redirect(url_for("auth.register"))

    return render_template(
        "register.html",
        is_first_user=first_user
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            flash("Login successful.", "success")

            return redirect(url_for("dashboard.dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("auth.login"))