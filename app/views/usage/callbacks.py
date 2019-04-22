#!/usr/bin/env python3

import docker
import pandas as pd
import dash_core_components as dcc
import plotly.graph_objs as go
import plotly.figure_factory as ff
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta
from flask import current_app, redirect, url_for
from sqlalchemy import and_
from app.extensions import db
from app.models import ActivityLog

def impute_stop_times(raw_data):
    """
    fill in missing container stop times.

    for containers that are currently running, stop_time is
    imputed to be the current time.
    for other records missing a stop_time due to some error,
    stop_time is imputed to be one day after start_time.
    """
    client = docker.from_env()
    df = raw_data.copy()
    for idx in df.loc[df.stop_time.isna()].index:
        if client.containers.get(idx): # container still running
            df.loc[idx, 'stop_time'] = datetime.utcnow()
        else:
            df.loc[idx, 'stop_time'] = df.loc[idx, 'start_time'] + \
                    timedelta(days=1)
    return df

def register_callbacks(dashapp):

    @dashapp.callback(Output('data-div', 'children'),
                      [Input('date-picker-range', 'start_date'),
                       Input('date-picker-range', 'end_date')])
    def data_query(start_date, end_date):
        """
        Read activity log table and filter results by selected date range.
        The jsonified results are returned to a hidden div.
        """
        if start_date and end_date:
            query = ActivityLog.query.filter(
                        and_(ActivityLog.start_time >= start_date,
                             ActivityLog.stop_time <= end_date))
            df = pd.read_sql(query.statement, db.session.bind,
                             parse_dates=['start_time', 'stop_time'],
                             index_col='id')
            imputed_df = impute_stop_times(df)
            return imputed_df.to_json(date_format='iso', orient='split')
        else:
            pass

    @dashapp.callback(Output('launched-containers-bar', 'figure'),
                      [Input('data-div', 'children')])
    def launched_containers_bar(jsonified_data):
        """
        create stacked bar chart counting number of launched containers
        by username and image_type
        """
        df = pd.read_json(jsonified_data, orient='split')
        if df.shape[0] > 0:
            data = []
            gp = pd.crosstab(df.username, df.image_type)
            for cname in gp.columns:
                data.append(go.Bar(x=gp.index, y=gp[cname], name=cname))
            layout = go.Layout(title='# of launched containers',
                               barmode="stack")
            return {"data": data, "layout": layout}
        else:
            return {"data": [{"x": [1, 2, 3], "y": [1, 2, 3]}]}

    @dashapp.callback(Output('utilization-gauge', 'value'),
                      [Input('data-div', 'children')],
                      [State('date-picker-range', 'start_date'),
                       State('date-picker-range', 'end_date')])
    def utilization_gauge(jsonified_data, start_date, end_date):
        """
        create gauge showing the utilization rate of the GPUs over
        the selected time period

        sum the runtime * num_gpus for all records in time period
        divided by the time in time period * 4
        """
        if start_date is not None:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date is not None:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        df = pd.read_json(jsonified_data, orient='split')
        if df.shape[0] > 0:
            used = ((df['stop_time'] - df['start_time']).dt.seconds * df['num_gpus']).sum()
            total = (end_date - start_date).total_seconds() * 4
            return used / total * 100
        else:
            return 0

    @dashapp.callback(Output('container-runtime-bar', 'figure'),
                      [Input('data-div', 'children')])
    def container_runtime_bar(jsonified_data):
        """
        create bar chart of total container runtime in hours
        by username for the selected time period
        """
        df = pd.read_json(jsonified_data, orient='split')
        if df.shape[0] > 0:
            df['runtime'] = df.stop_time - df.start_time
            gp = df.groupby('username')['runtime'].sum().dt.total_seconds() / 3600
            data = [go.Bar(x=gp.index, y=gp.values)]
            layout = go.Layout(title="total container runtime (hrs)")
            return {"data": data, "layout": layout}
        else:
            return {"data": [{"x": [1, 2, 3], "y": [1, 2, 3]}]}

    @dashapp.callback(Output('aws-cost', 'children'),
                      [Input('data-div', 'children')])
    def aws_cost_comparison(jsonified_data):
        """
        calculate the total cost of GPU utilization if run on AWS
        for the selected time period. the calculated cost will be
        an over-estimate as it does not account for the time that
        users leave containers idle. if an equivalent workload were
        run on AWS, users would ideally stop the instance when not
        actively using it.
        """
        df = pd.read_json(jsonified_data, orient='split')
        HOURLY_COST = 3.06 # hourly cost of p3.2xlarge instance as of 22APR2019
        if df.shape[0] > 0:
            df['runtime'] = df.stop_time - df.start_time
            gpu_containers = df.loc[df.num_gpus > 0]
            gpu_hours = gpu_containers['runtime'].sum().total_seconds() / 3600
            cost = gpu_hours * HOURLY_COST
            return "${:0,.2f}".format(cost)
        else:
            return "$0.00"

    @dashapp.callback(Output('container-gantt-chart', 'figure'),
                      [Input('data-div', 'children')])
    def container_gantt_chart(jsonified_data):
        """
        create a gantt chart showing a timeline of launched containers
        by username and image_type for the selected time period.
        """
        df = pd.read_json(jsonified_data, orient='split')
        if df.shape[0] > 0:
            df.rename(columns={'username': 'Task', 'start_time': 'Start',
                               'stop_time': 'Finish', 'image_type': 'Resource'},
                      inplace=True)
            fig = ff.create_gantt(df=df, index_col='Resource',
                                  group_tasks=True, showgrid_x=True,
                                  showgrid_y=True, width='100%', title='Container History')
            fig['layout'].update(width=None, height=None, autosize=True)
            fig['layout']['xaxis'].update(autorange=True)
            fig['layout']['yaxis'].update(autorange=True)
            return fig
