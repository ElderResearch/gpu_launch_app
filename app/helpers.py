#!/usr/bin/python3

import random
import secrets
from datetime import datetime, timedelta

import dateutil.parser
import docker
import pandas as pd
from numpy.random import exponential
from sqlalchemy import and_, or_

from app import db
from app.models import ActivityLog, User


def generate_usage_log_data(Model, n=100):
    _names = ["andy", "betty", "bobby", "timmy", "sue"]
    _imagetypes = ["Python", "Python+R"]
    _numgpus = [0, 1, 2, 3, 4]
    containers = []

    for i in range(n):
        td_start = timedelta(days=i % 30, hours=random.randint(0, 23))
        start = datetime.utcnow() - td_start
        instance = Model(
            id=secrets.token_hex(32),
            username=random.choice(_names),
            image_type=random.choice(_imagetypes),
            num_gpus=random.choice(_numgpus),
            start_time=start,
            stop_time=start + timedelta(hours=exponential(8)),
        )
        containers.append(instance)

    return containers


def impute_stop_times(raw_data, start_date):
    """
    fill in missing container stop times.

    for containers that are currently running, stop_time is
    imputed to be the current time.
    for other records missing a stop_time due to some error,
    stop_time is imputed to be one day after start_time.
    """
    client = docker.from_env()
    running = [c.id for c in client.containers.list(sparse=True)]
    df = raw_data.copy()
    for idx in df.loc[df.stop_time.isna()].index:
        if idx in running:  # container still running
            df.loc[idx, "stop_time"] = datetime.utcnow()
        else:
            delta = timedelta(days=1)
            df.loc[idx, "stop_time"] = df.loc[idx, "start_time"] + delta

    df = df.loc[df["stop_time"] > start_date]
    return df


def trim_start_stop(raw_data, start_date, end_date):
    """
    trim the container start and/or stop times to fit in selected date range
    """
    df = raw_data.copy()
    mask = (df.start_time < start_date) & (df.stop_time > start_date)
    df.loc[mask, "start_time"] = start_date
    df.loc[df.stop_time > end_date, "stop_time"] = end_date

    return df


def data_query(start_date, end_date, impute_dates=True, trim_dates=True):
    """
    Read activity log table and filter results by selected date range.
    The jsonified results are returned to a hidden div.
    """
    start_date = dateutil.parser.parse(start_date, ignoretz=True)
    end_date = dateutil.parser.parse(end_date, ignoretz=True)
    query = db.session.query(ActivityLog, User.username).join(User)
    query = query.filter(
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
    df = pd.read_sql(
        query.statement,
        db.session.bind,
        parse_dates=["start_time", "stop_time"],
        index_col="id",
    )
    if impute_dates:
        df = impute_stop_times(df, start_date)
    if trim_dates:
        df = trim_start_stop(df, start_date, end_date)
    df["runtime"] = (df.stop_time - df.start_time).dt.total_seconds() / 3600
    df["gpu_hours"] = df["runtime"] * df["num_gpus"]
    return df.to_json(orient="records", date_format="iso")
