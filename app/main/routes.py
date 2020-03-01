from datetime import datetime
from urllib.parse import urlparse

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import launch
from app import db
from app.main import bp
from app.models import ActivityLog

FLASH_CLS = {
    "error": "alert alert-danger",
    "success": "alert alert-success",
}


@bp.context_processor
def process_context():
    def container_url(port):
        u = urlparse(url_for("main.index", _external=True))
        if u.port:
            return u._replace(netloc=u.netloc.replace(str(u.port), str(port))).geturl()
        else:
            return "{}:{}{}".format(u._replace(path="").geturl(), port, u.path)

    return dict(container_url=container_url)


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen == datetime.utcnow()
        db.session.commit()


@bp.route("/", methods=["GET"])
@login_required
def index():
    launched_sessions = launch.active_eri_images(ignore_other_images=True)

    return render_template(
        "main/index.html",
        launched_sessions=launched_sessions,
        sessoptions=sorted(launch.ERI_IMAGES.keys()),
        num_avail_gpus=list(range(len(launch._get_avail_devices()) + 1)),
        images=launch.ERI_IMAGES,
    )


@bp.route("/createSession", methods=["POST"])
@login_required
def create_session():
    resp = launch.launch(
        username=current_user.username,
        password_hash=current_user.password_hash,
        imagetype=request.form["imagetype"],
        num_gpus=request.form["num_gpus"],
    )

    # handle errors
    if resp.get("error", False):
        flash(
            message=resp.get("message", "unhandled error"), category=FLASH_CLS["error"]
        )
        return redirect(url_for("home.index"))

    flash(
        message="docker container {} created successfully".format(resp["id"][:10]),
        category=FLASH_CLS["success"],
    )
    entry = ActivityLog(
        id=resp["id"],
        username=current_user.username,
        image_type=resp["imagetype"],
        num_gpus=resp["num_gpus"],
    )
    db.session.add(entry)
    db.session.commit()
    return redirect(url_for("main.index"))


@bp.route("/killSession", methods=["POST"])
@login_required
def kill_session():
    """
    Method allowing users to kill their containers
    Admins can kill any container
    """
    # TODO: Modify this function for logged-in user or admin password
    # verify that the password they provided hashes to the same value as the
    # known pw hash

    entry = ActivityLog.query.filter_by(id=request.form["docker_id"]).first()

    if entry is not None:
        if current_user.username == entry.username or current_user.is_admin():
            resp = launch.kill(docker_id=request.form["docker_id"])
            # handle errors
            if resp.get("error", False):
                flash(
                    message=resp.get("message", "unhandled error"),
                    category=FLASH_CLS["error"],
                )
                return redirect(url_for("main.index"))
            entry.stop()
            db.session.commit()
            flash(
                message="docker container {} killed successfully".format(
                    request.form["docker_id"][:10]
                ),
                category=FLASH_CLS["success"],
            )
    else:
        if current_user.is_admin():
            resp = launch.kill(docker_id=request.form["docker_id"])
            # handle errors
            if resp.get("error", False):
                flash(
                    message=resp.get("message", "unhandled error"),
                    category=FLASH_CLS["error"],
                )
                return redirect(url_for("main.index"))
            flash(
                message="docker container {} killed successfully".format(
                    request.form["docker_id"][:10]
                ),
                category=FLASH_CLS["success"],
            )
        else:
            flash(
                message=(
                    "unable to kill session. if this is your container and the"
                    " problem persists, contact admin for assistance"
                ),
                category=FLASH_CLS["error"],
            )
    return redirect(url_for("main.index"))
