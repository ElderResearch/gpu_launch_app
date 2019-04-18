#!/usr/bin/env python3

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from datetime import date, datetime, timedelta

layout = dbc.Container(
    [
        dbc.Row([
            dbc.Col([
                html.H3('Select Date Range'),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    min_date_allowed=date(2019, 3, 2),
                    max_date_allowed=datetime.date(datetime.utcnow()),
                    start_date=max(
                        date(2019, 3, 2),
                        datetime.date(datetime.utcnow() - timedelta(days=30))),
                    end_date=datetime.date(datetime.utcnow()),
                    style={"margin-top": 10}
                )
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='graph-1')
            ]),
            dbc.Col([
                daq.Gauge(
                    id='utilization-gauge',
                    showCurrentValue=True,
                    units="%",
                    label='GPU Utilization',
                    color={
                        "gradient": True, 
                        "ranges": {
                            "red": [0, 25], 
                            "yellow": [25, 75], 
                            "green": [75, 100]
                        }
                    },
                    min=0,
                    max=100,
                    value=0,
                    size=350
                    )
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='graph-3')
            ]),
            dbc.Col([
                html.H3('AWS Cost Comparison'),
                html.P(
                    '''\
Based on the p3.2xlarge EC2 instance, GPU usage during the selected
timeframe would have incurred a total cost of'''),
                html.H4(id='aws-cost'),
                html.P(
                    '''\
This cost is not adjusted for the amount of time that GPU Box
containers are left idle.'''),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(
                    dcc.Graph(id='gantt-chart')
                )
            ],
            width=12)
        ]),

        # hidden div for holding data
        dbc.Row(dbc.Col(html.Div(id='data-div', style={'display': 'none'})))
    ],
    fluid=True,
    className="mt-4"
)
