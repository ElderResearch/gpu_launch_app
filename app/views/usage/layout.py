#!/usr/bin/env python3

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from flask import url_for

navbar = dbc.NavbarSimple(
    [
        dbc.NavItem(dbc.NavLink("Home", href=url_for('home.index')))
    ],
    brand="DC GPU Machine Usage",
    brand_href='#',
    sticky='top'
)

body = dbc.Container(
    [
        dbc.Row([
            dbc.Col([
                html.H2('Graph 1'),
                dcc.Graph(id='graph-1')
            ]),
            dbc.Col([
                html.H2('Graph 2'),
                dcc.Graph(id='graph-2')
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.H2('Graph 3'),
                dcc.Graph(id='graph-3')
            ]),
            dbc.Col([
                html.H2('Graph 4'),
                dcc.Graph(id='graph-4')
            ]),
        ]),
    ]
)
