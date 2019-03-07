import hashlib
import os
from notebook.auth.security import passwd, passwd_check

from flask import Blueprint, flash, redirect, render_template, request, url_for
from .. import launch
from ..extensions import db
from ..models import ActivityLog

HISTORY = []
LAUNCHED_SESSIONS = []
FLASH_CLS = {
    'error': "alert alert-danger",
    'success': "alert alert-success",
}

home = Blueprint('home', __name__)

@home.route('/', methods=['GET'])
def index():
    launched_sessions = launch.active_eri_images(ignore_other_images=True)

    return render_template(
        'index.html',
        launched_sessions=launched_sessions,
        sessoptions=sorted(launch.ERI_IMAGES.keys()),
        num_avail_gpus=list(range(len(launch._get_avail_devices()) + 1))
    )


@home.route('/createSession', methods=['POST'])
def create_session():
    resp = launch.launch(
        username=request.form['username'],
        imagetype=request.form['imagetype'],
        password=request.form['password'],
        num_gpus=request.form['num_gpus']
    )
    HISTORY.append(resp)

    # handle errors
    if resp.get('error', False):
        flash(
            message=resp.get('message', 'unhandled error'),
            category=FLASH_CLS['error']
        )
        return redirect(url_for('home.index'))

    flash(
        message="docker container {} created successfully".format(
            resp['id'][:10]
        ),
        category=FLASH_CLS['success']
    )
    entry = ActivityLog(id=resp['id'], username=resp['username'],
                        image_type=resp['imagetype'], num_gpus=resp['num_gpus'])
    db.session.add(entry)
    db.session.commit()
    return redirect(url_for('home.index'))


@home.route('/killSession', methods=['POST'])
def kill_session():
    # verify that the password they provided hashes to the same value as the
    # known pw hash
    if not passwd_check(request.form['pwhash'], request.form['password']):
        flash(
            message=(
                "unable to kill session - incorrect password. if this is"
                " your container and you have forgotten the password, contact"
                " admin for e"
            ),
            category=FLASH_CLS['error']
        )
        return redirect(url_for('home.index'))

    resp = launch.kill(docker_id=request.form['docker_id'])
    HISTORY.append(resp)

    # handle errors
    if resp.get('error', False):
        flash(
            message=resp.get('message', 'unhandled error'),
            category=FLASH_CLS['error']
        )
        return redirect(url_for('home.index'))

    flash(
        message="docker container {} killed successfully".format(
            request.form['docker_id'][:10]
        ),
        category=FLASH_CLS['success']
    )
    entry = ActivityLog.query.filter_by(id=request.form["docker_id"]).first()
    if entry is not None:
        entry.stop()
        db.session.commit()
    return redirect(url_for('home.index'))
