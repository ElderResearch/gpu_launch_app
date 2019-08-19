from datetime import datetime
import pam
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from .. import launch
from ..extensions import db, cache
from ..forms import LoginForm
from ..models import ActivityLog, User
from ..helpers import data_query

FLASH_CLS = {
    'error': "alert alert-danger",
    'success': "alert alert-success",
}

home = Blueprint('home', __name__)

@home.context_processor
def process_context():

    def container_url(port):
        u = urlparse(url_for('home.index', _external=True))
        if u.port:
            return u._replace(netloc=u.netloc.replace(str(u.port), str(port))).geturl()
        else:
            return "{}:{}{}".format(u._replace(path='').geturl(), port, u.path)

    return dict(container_url=container_url)

@home.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen == datetime.utcnow()
        db.session.commit()

@home.route('/', methods=['GET'])
@login_required
def index():
    launched_sessions = launch.active_eri_images(ignore_other_images=True)

    return render_template(
        'index.html',
        launched_sessions=launched_sessions,
        sessoptions=sorted(launch.ERI_IMAGES.keys()),
        num_avail_gpus=list(range(len(launch._get_avail_devices()) + 1))
    )


@home.route('/createSession', methods=['POST'])
@login_required
def create_session():
    resp = launch.launch(
        username=current_user.username,
        password_hash=current_user.password_hash,
        imagetype=request.form['imagetype'],
        num_gpus=request.form['num_gpus']
    )

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
    entry = ActivityLog(id=resp['id'], username=current_user.username,
                        image_type=resp['imagetype'], num_gpus=resp['num_gpus'])
    db.session.add(entry)
    db.session.commit()
    cache.delete_memoized(data_query)
    return redirect(url_for('home.index'))


@home.route('/killSession', methods=['POST'])
@login_required
def kill_session():
    ## TODO: Modify this function for logged-in user or admin password
    # verify that the password they provided hashes to the same value as the
    # known pw hash
    entry = ActivityLog.query.filter_by(id=request.form["docker_id"]).first()
    if entry is not None:
        if current_user.username == entry.username or current_user.is_admin():
            resp = launch.kill(docker_id=request.form['docker_id'])
            # handle errors
            if resp.get('error', False):
                flash(
                    message=resp.get('message', 'unhandled error'),
                    category=FLASH_CLS['error']
                )
                return redirect(url_for('home.index'))
            entry.stop()
            db.session.commit()
            cache.delete_memoized(data_query)
            flash(
                message="docker container {} killed successfully".format(
                    request.form['docker_id'][:10]
                ),
                category=FLASH_CLS['success']
            )
    else:
        flash(
            message=(
                "unable to kill session. if this is your container and the"
                " problem persists, contact admin for assistance"
            ),
            category=FLASH_CLS['error']
        )
    return redirect(url_for('home.index'))

@home.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None:
                if pam.authenticate(form.username.data, form.password.data):
                    try:
                        user = User(username=form.username.data)
                        user.set_password_hash(form.password.data)
                        db.session.add(user)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        flash(message=("Error adding user to database. "
                                       "Contact an admin for assistance."),
                              category=FLASH_CLS['error'])
                        return redirect(url_for('home.login'))
                else:
                    flash(message="Invalid username or password",
                          category=FLASH_CLS['error'])
                    return redirect(url_for('home.login'))
            if not user.check_password(form.password.data):
                flash(message="Invalid username or password",
                      category=FLASH_CLS['error'])
                return redirect(url_for('home.login'))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('home.index')
            return redirect(next_page)
        else:
            flash(message="All fields required.", category=FLASH_CLS['error'])
    return render_template('login.html', form=form)

@home.route('/dashboard', methods=["GET"])
@login_required
def dashboard():
    return render_template('dashboard.html')

@home.route('/data', methods=["GET"])
@login_required
def data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    return data_query(start_date, end_date)

@home.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home.login'))
