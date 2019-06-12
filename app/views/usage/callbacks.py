#!/usr/bin/env python3

import docker
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.graph_objs as go
import plotly.figure_factory as ff
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta
from flask import current_app, redirect, url_for
from sqlalchemy import and_, or_, between
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
    running = [c.id for c in client.containers.list(sparse=True)]
    df = raw_data.copy()
    for idx in df.loc[df.stop_time.isna()].index:
        if idx in running: # container still running
            df.loc[idx, 'stop_time'] = datetime.utcnow()
        else:
            df.loc[idx, 'stop_time'] = df.loc[idx, 'start_time'] + \
                    timedelta(days=1)
    return df

def trim_start_stop(raw_data, start_date, end_date):
    """
    trim the container start and/or stop times to fit in the selected date range
    """
    df = raw_data.copy()
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    df.loc[df.start_time < start_date, 'start_time'] = start_date
    df.loc[df.stop_time > end_date, 'stop_time'] = end_date

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
                    or_(and_(ActivityLog.start_time.__le__(start_date),
                             or_(ActivityLog.stop_time.__eq__(None),
                                 ActivityLog.stop_time.__gt__(end_date))),
                        or_(ActivityLog.start_time.between(start_date, end_date),
                            ActivityLog.stop_time.between(start_date, end_date))
                        )
                    )
            df = pd.read_sql(query.statement, db.session.bind,
                             parse_dates=['start_time', 'stop_time'],
                             index_col='id')
            df = impute_stop_times(df)
            df = trim_start_stop(df, start_date, end_date)
            df['runtime'] = (df.stop_time - df.start_time).dt.total_seconds() / 3600
            df['gpu_hours'] = df['runtime'] * df['num_gpus']

            return df.to_json(date_format='iso', orient='split')
        else:
            pass


    @dashapp.callback(Output('launched-containers-bar', 'children'),
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
                data.append(go.Bar(x=gp.index, y=gp[cname], name=cname, 
                    showlegend=False, hoverinfo='y+name'))
            layout = go.Layout(barmode="stack")

            return [dcc.Graph(figure={"data": data, "layout": layout})]


    @dashapp.callback(Output('gpu-utilization', 'children'),
                      [Input('data-div', 'children')],
                      [State('date-picker-range', 'start_date'),
                       State('date-picker-range', 'end_date')])
    def gpu_utilization(jsonified_data, start_date, end_date):
        """
        calculate utilization rate of the GPUs over the selected time period

        sum the runtime * num_gpus for all records in time period
        divided by the time in time period * 4
        """
        if start_date is not None:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date is not None:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        df = pd.read_json(jsonified_data, orient='split')
        if df.shape[0] > 0:
            poss_gpu_hrs = (end_date - start_date).total_seconds() / 3600 * 4

            return "{:.0%}".format(df['gpu_hours'].sum()/poss_gpu_hrs)


    @dashapp.callback(Output('container-runtime-bar', 'children'),
                      [Input('data-div', 'children')])
    def container_runtime_bar(jsonified_data):
        """
        create bar chart of total container runtime in hours
        by username for the selected time period
        """
        df = pd.read_json(jsonified_data, orient='split')
        if df.shape[0] > 0:
            gp = df.groupby('username')['runtime'].sum()
            gp = gp.round(2)
            gp = gp.loc[gp.values > 0]
            text = ['{:.2f}'.format(v) for v in gp.values]
            data = [go.Bar(x=gp.index, y=gp.values, 
                hoverinfo='text', text=text)]

            return [dcc.Graph(figure={"data": data})]


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
            cost = df['gpu_hours'].sum() * HOURLY_COST

            return "${:0,.2f}".format(cost)


    @dashapp.callback(Output('container-gantt-chart', 'children'),
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
            figure = ff.create_gantt(df=df, index_col='Resource',
                                     group_tasks=True, showgrid_x=True,
                                     showgrid_y=True, width='100%', title='')
            figure['layout'].update(width=None, height=None, autosize=True)
            figure['layout']['xaxis'].update(autorange=True)
            figure['layout']['yaxis'].update(autorange=True)

            return [dcc.Graph(figure=figure)]


    @dashapp.callback(Output('total-containers', 'children'),
                      [Input('data-div', 'children')])
    def total_containers(jsonified_data):
        """
        calculate total number of launched containers in selected time period
        """
        df = pd.read_json(jsonified_data, orient='split')

        return ["{:,}".format(df.shape[0])]


    @dashapp.callback(Output('total-hours', 'children'),
                      [Input('data-div', 'children')])
    def total_hours(jsonified_data):
        """
        calculate total container runtime hours in selected time period
        """
        df = pd.read_json(jsonified_data, orient='split')
        if df.shape[0] > 0:
            total = df['runtime'].sum()

            return ["{:.0f}".format(total)]


    @dashapp.callback(Output('gpu-utilization-bar', 'children'),
                      [Input('data-div', 'children')],
                      [State('date-picker-range', 'start_date'),
                       State('date-picker-range', 'end_date')])
    def gpu_utilization_bar(jsonified_data, start_date, end_date):
        """
        calculate utilization rate of the GPUs over the selected time period

        sum the runtime * num_gpus for all records in time period
        divided by the time in time period * 4
        """
        if start_date is not None:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date is not None:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        df = pd.read_json(jsonified_data, orient='split')
        if df.shape[0] > 0:
            poss_gpu_hrs = (end_date - start_date).total_seconds() / 3600 * 4
            gp = df.groupby('username')['gpu_hours'].sum() / poss_gpu_hrs * 100
            gp = gp.round(2)
            gp = gp.loc[gp.values > 0]
            text = ['{:.2f}%'.format(v) for v in gp.values]
            data = [go.Bar(x=gp.index, y=gp.values,
                hoverinfo='text', text=text)]

            return [dcc.Graph(figure={"data": data})]


    @dashapp.callback(Output('gpu-utilization-pie', 'children'),
                      [Input('data-div', 'children')],
                      [State('date-picker-range', 'start_date'),
                       State('date-picker-range', 'end_date')])
    def gpu_utilization_pie(jsonified_data, start_date, end_date):
        """
        calculate absolute utilization of the GPUs over the selected time period

        sum the runtime * num_gpus for all records in time period
        """
        if start_date is not None:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date is not None:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        df = pd.read_json(jsonified_data, orient='split')
        if df.shape[0] > 0:
            gp = df.groupby('username')['gpu_hours'].sum()
            gp = gp.round(1)
            gp = gp.loc[gp.values > 0]
            data = [go.Pie(labels=gp.index, values=gp.values,
                           hoverinfo='label+percent', textinfo='value')]

            return [dcc.Graph(figure={"data": data})]
