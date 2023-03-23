import os
import pandas as pd
import numpy as np
import dash
import datetime
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from sdk import SedmaxHeader, Sedmax, ElectricalArchive
from sankey.prepare_data_new import load_data, sankey_plot

# Create a dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash(__name__, external_stylesheets=['sankey/assets/bootstrap.min.css'])
app.title = 'Диаграмма Sankey'
s = Sedmax('https://demo.sedmax.ru')

username = 'demo'  # os.environ['SEDMAX_USERNAME']
password = 'demo'  # os.environ['SEDMAX_PASSWORD']
s.login(username, password)

el = ElectricalArchive(s)

# background_color = '#5f8dab'
background_color = '#ffffff'

update_button = dbc.Button("Обновить", id="update_", n_clicks=0, className="ant-electro-btn-primary",
                           style={'margin-right': '3px', 'font-family': 'sans-serif', 'font-size': '14px'}
                           )

date_picker = html.Div([
    html.B(' Электроснабжение офиса. Диаграмма Sankey распределения активной энергии',
           style={'text-align': 'center', 'color': '#ffffff', 'font-size': 22, 'margin-left': '1%'}),
    html.Div([update_button,
              dcc.DatePickerRange(
                  id='date-picker-range',
                  initial_visible_month=datetime.datetime.now().date(),
                  start_date=(datetime.datetime.now() - pd.Timedelta(days=1)).date(),
                  end_date=datetime.datetime.now().date(),
                  # month_format='MM/YYYY',
              )], style={'float': 'right', 'padding': '1px'})
],
    style={'margin-top': '1px', 'margin-bottom': '0px',
           'backgroundColor': "grey", 'box-shadow': '0 0 2px 2px rgba(0,0,0,0.3)'}
)

# Create an app layout
body = dbc.Container([
    dbc.Row([dcc.Graph(id='sankey_plot', animate=False,
                       config={'displaylogo': False})], style={'padding': '5px'}),
    html.Br()
], fluid=True, style={'background-color': background_color})

app.layout = html.Div(children=[
    SedmaxHeader(title='', logo='sedmax'),
    dcc.Store(id='memory-output'),
    dbc.Row(date_picker, style={'background-color': background_color}),
    html.Div(id='app_body', children=[body],
             style={'margin-top': '4px', 'height': 'calc(100vh - 98px)', 'overflowY': 'scroll',
                    'box-shadow': '0 1px 4px 1px rgba(0,0,0,0.2)', 'margin': '3px'}),
], style={'position': 'fixed', 'width': '100%', 'z-index': '1', 'hight': 'calc(100% - 100px)'})


@app.callback([Output(component_id='memory-output', component_property='data')],
              [State('date-picker-range', 'start_date'),
               State('date-picker-range', 'end_date'),
               Input('update_', 'n_clicks')]
              )
def update_data(start_date, end_date, n):
    print(start_date)
    start_date = start_date + ' 00:00:00'
    end_date = end_date + ' 23:59:59'
    data = load_data(s, start_date, end_date)
    return data


@app.callback(
    [Output(component_id='sankey_plot', component_property='figure')],
    [Input(component_id='memory-output', component_property='data')]
)
def sankey_figure(data):
    fig = sankey_plot(data)
    return [fig]
