#!/usr/bin/python3

import random
import secrets
from datetime import datetime, timedelta

import dateutil.parser
import docker
from flask import jsonify
from numpy.random import exponential
from sqlalchemy import and_, or_

from app.models import ActivityLog, User


def generate_usage_log_data(n=100):
    _names = ["andy", "betty", "bobby", "timmy", "sue"]
    _imagetypes = ["Python", "Python+R"]
    _numgpus = [0, 1, 2, 3, 4]
    containers = []

    for i in range(n):
        user = User(username=random.choice(_names))
        td_start = timedelta(days=i % 30, hours=random.randint(0, 23))
        start = datetime.utcnow() - td_start
        instance = ActivityLog(
            id=secrets.token_hex(32),
            user=user,
            image_type=random.choice(_imagetypes),
            num_gpus=random.choice(_numgpus),
            start_time=start,
            stop_time=start + timedelta(hours=exponential(8)),
        )
        containers.append(instance)

    return containers


def impute_stop_times(logs, start_date):
    """
    fill in missing container stop times.

    for containers that are currently running, stop_time is
    imputed to be the current time.
    for other records missing a stop_time due to some error,
    stop_time is imputed to be one day after start_time.
    """
    client = docker.from_env()
    running = [c.id for c in client.containers.list(sparse=True)]
    for log in logs:
        if log.stop_time is None:
            if log.id in running:  # container still running
                log.stop()
            else:
                delta = timedelta(days=1)
                log.stop_time = log.start_time + delta

    return [log for log in logs if log.stop_time > start_date]


def trim_start_stop(logs, start_date, end_date):
    """
    trim the container start and/or stop times to fit in selected date range
    """
    for log in logs:
        if log.start_time < start_date and log.stop_time > start_date:
            log.start_time = start_date
    if log.stop_time > end_date:
        log.stop_time = end_date

    return logs


def data_query(start_date, end_date, impute_dates=True, trim_dates=True):
    """
    Read activity log table and filter results by selected date range.
    The jsonified results are returned to a hidden div.
    """
    start_date = dateutil.parser.parse(start_date, ignoretz=True)
    end_date = dateutil.parser.parse(end_date, ignoretz=True)
    query = ActivityLog.query.filter(
        or_(
            and_(
                ActivityLog.start_time.__le__(start_date),
                or_(
                    ActivityLog.stop_time.__eq__(None),
                    ActivityLog.stop_time.__gt__(end_date),
                ),
            ),
            or_(
                ActivityLog.start_time.between(start_date, end_date),
                ActivityLog.stop_time.between(start_date, end_date),
            ),
        )
    )
    logs = query.all()
    if impute_dates:
        logs = impute_stop_times(logs, start_date)
    if trim_dates:
        logs = trim_start_stop(logs, start_date, end_date)
    # TODO: implement these calculations in javascript
    # df["runtime"] = (df.stop_time - df.start_time).dt.total_seconds() / 3600
    # df["gpu_hours"] = df["runtime"] * df["num_gpus"]
    return jsonify([log.serialize for log in logs])
