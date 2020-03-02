from flask import render_template, request, jsonify
from flask_login import login_required

from app.dashboard import bp
from app.helpers import data_query
from app.models import ActivityLog


@bp.route("/", methods=["GET"])
@login_required
def dashboard():
    return render_template("dashboard/dashboard.html")


@bp.route("/data", methods=["GET"])
@login_required
def data():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    return data_query(start_date, end_date)


@bp.route("/history", methods=["GET"])
@login_required
def history():
    page = request.args.get("page")
    per_page = request.args.get("per_page")
    query = (
        ActivityLog.query(ActivityLog)
        .order_by(ActivityLog.start_time.desc())
        .paginate(page=page, per_page=per_page)
    )
    return jsonify([item.serialize for item in query.items])
