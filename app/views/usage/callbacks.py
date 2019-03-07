#!/usr/bin/env python3

from dash.dependencies import Input, Output

def register_callbacks(dashapp):
    @dashapp.callback(Output('graph-1', 'figure'),
                      [Input('some-input', 'value')])
    def my_first_callback(value):
        return {"data": [{"x": [1, 2, 3], "y": [3, 2, 6]}]}

    @dashapp.callback(Output('graph-2', 'figure'),
                      [Input('some-input', 'value')])
    def my_second_callback(value):
        return {"data": [{"x": [1, 2, 3], "y": [2, 3, 7]}]}

    @dashapp.callback(Output('graph-3', 'figure'),
                      [Input('some-input', 'value')])
    def my_third_callback(value):
        return {"data": [{"x": [1, 2, 3], "y": [1, 4, -3]}]}

    @dashapp.callback(Output('graph-4', 'figure'),
                      [Input('some-input', 'value')])
    def my_fourth_callback(value):
        return {"data": [{"x": [1, 2, 3], "y": [1, 3, 5]}]}
