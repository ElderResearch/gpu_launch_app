from flask import render_template, request
from flask_login import login_required

from app.dashboard import bp
from app.helpers import data_query


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
