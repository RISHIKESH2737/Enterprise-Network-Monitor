from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import db

settings_bp = Blueprint("settings", __name__)

# In-memory alert config (replace with DB model for persistence)
_alert_configs = {}


def get_alert_cfg(user_id):
    return _alert_configs.get(user_id, {
        "email_alerts": False,
        "alert_email": ""
    })


def save_alert_cfg(user_id, cfg):
    _alert_configs[user_id] = cfg


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "email_alerts":
            email_alerts = "email_alerts" in request.form
            alert_email  = request.form.get("alert_email", "").strip()

            save_alert_cfg(current_user.id, {
                "email_alerts": email_alerts,
                "alert_email":  alert_email
            })

            flash("Alert settings saved successfully.", "success")

        elif form_type == "change_password":
            current_password = request.form.get("current_password", "")
            new_password     = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not check_password_hash(current_user.password, current_password):
                flash("Current password is incorrect.", "error")
            elif len(new_password) < 6:
                flash("New password must be at least 6 characters.", "error")
            elif new_password != confirm_password:
                flash("New passwords do not match.", "error")
            else:
                current_user.password = generate_password_hash(new_password)
                db.session.commit()
                flash("Password updated successfully.", "success")

        return redirect(url_for("settings.settings_page"))

    # GET
    alert_cfg = get_alert_cfg(current_user.id)
    # Pre-fill alert email from user account if not set
    if not alert_cfg.get("alert_email"):
        alert_cfg["alert_email"] = current_user.email

    return render_template(
        "settings.html",
        username=current_user.username,
        user_role=current_user.role,
        alert_cfg=alert_cfg
    )