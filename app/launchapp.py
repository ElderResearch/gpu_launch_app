from datetime import datetime
import os
from notebook.auth.security import passwd, passwd_check

from . import launch
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask('docker_launcher', template_folder='/var/www/gpu_launch_app/app/templates')
app.secret_key = '\xc8d\x19E}\xa5g\xbbC\xbd\xe2\x17\x83\xfa!>\xead\x07p\xbd\x92\xce\x85'
app.debug = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,
                                                                    'app.db')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class ActivityLog(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(32))
    image_type = db.Column(db.String(8))
    num_gpus = db.Column(db.Integer)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    stop_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return "<ActivityLog {}".format(self.id)

    def stop(self):
        self.stop_time = datetime.utcnow()

HISTORY = []
LAUNCHED_SESSIONS = []
FLASH_CLS = {
    'error': "alert alert-danger",
    'success': "alert alert-success",
}


@app.route('/', methods=['GET'])
def home():
    launched_sessions = launch.active_eri_images(ignore_other_images=True)

    return render_template(
        'index.html',
        launched_sessions=launched_sessions,
        sessoptions=sorted(launch.ERI_IMAGES.keys()),
        num_avail_gpus=list(range(len(launch._get_avail_devices()) + 1))
    )


@app.route('/createSession', methods=['POST'])
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
        return redirect(url_for('home'))

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
    return redirect(url_for('home'))


@app.route('/killSession', methods=['POST'])
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
        return redirect(url_for('home'))

    resp = launch.kill(docker_id=request.form['docker_id'])
    HISTORY.append(resp)

    # handle errors
    if resp.get('error', False):
        flash(
            message=resp.get('message', 'unhandled error'),
            category=FLASH_CLS['error']
        )
        return redirect(url_for('home'))

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
    return redirect(url_for('home'))


if __name__ == '__main__':
    try:
        db.create_all()
    except Exception as e:
        pass
    app.run(debug=False, host="0.0.0.0")
