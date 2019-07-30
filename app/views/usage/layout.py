#!/usr/bin/env python3

import dash_core_components as dcc
import dash_html_components as html
from datetime import date, datetime, timedelta

def key_metric_card(id, title, default_value='', subtext=''):
    return html.Div([
            html.Div([
                html.H4(title, className='my-0 font-weight-normal')
            ], className='card-header'),
            html.Div([
                html.H1([
                    default_value
                ], className='card-title', id=id),
                html.Small(subtext, className='text-muted')
            ], className='card-body')
    ], className="card mb-4 shadow-sm")

def graph_card(id, title):
    return html.Div([
            html.Div([
                html.H4(title, className='my-0 font-weight-normal')
            ], className='card-header'),
            html.Div(dcc.Graph(), id=id, className='card-img-top')
    ], className="card mb-4 shadow-sm")

navbar = html.Div([
    html.A(
        html.H4("gpu launch app"),
        href='/', className="my-0 mr-md-auto font-weight-normal text-muted"),

    dcc.DatePickerRange(
                id='date-picker-range',
                updatemode='bothdates',
                min_date_allowed=date(2019, 3, 2),
                max_date_allowed=datetime.date(datetime.utcnow() + timedelta(days=1)),
                start_date=datetime.date(datetime.utcnow() - timedelta(days=30)),
                end_date=datetime.date(datetime.utcnow() + timedelta(days=1)),
    )
], className="d-flex flex-column flex-md-row align-items-center p-3 px-md-4 mb-3 bg-white border-bottom shadow-sm")

body = html.Div([
    html.Div([
        key_metric_card(id='total-containers', title='Containers',
                        default_value='0'),
        key_metric_card(id='total-hours', title='Runtime (hrs)',
                        default_value='0'),
        key_metric_card(id='gpu-utilization', title='GPU Utilization',
                        default_value='0%'),
        key_metric_card(id='aws-cost', title='AWS Savings',
                        default_value='$0',
                        subtext='based on p3.2xlarge instance'),
    ], className='card-deck text-center'),
    html.Div([
        graph_card(id='container-gantt-chart',
                   title='Container Timeline'),
    ], className='card-deck text-center'),
    html.Div([
        graph_card(id='launched-containers-bar',
                   title='Containers'),
        graph_card(id='container-runtime-bar',
                   title='Runtime (hrs)'),
    ], className='card-deck text-center'),
    html.Div([
        graph_card(id='gpu-utilization-pie',
                   title='Total GPU Usage (gpu-hrs)'),
        graph_card(id='gpu-utilization-bar',
                   title='GPU Utilization Rate per User'),
    ], className='card-deck text-center'),

    html.Div(id='data-div', style={'display': 'none'})
], className='container')

layout = html.Div([navbar, body], id='main-div')
