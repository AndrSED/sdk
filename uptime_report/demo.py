import os
import pandas as pd
import numpy as np
import dash
import datetime
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_treeview_antd

from sdk import SedmaxHeader, Sedmax, ElectricalArchive, EventJournal
from uptime_report.graphs import out_time_scatter, out_table
from uptime_report.modules import pq_devices, report_by_device, report, uptime_table, empty_plot

import locale
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

# Create a dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash(__name__, external_stylesheets=['uptime_report/assets/bootstrap.min.css'])
app.title = 'Отчёт ККЭ'
s = Sedmax('https://demo.sedmax.ru')

username = 'demo' #os.environ['SEDMAX_USERNAME']
password = 'demo' #os.environ['SEDMAX_PASSWORD']
s.login(username, password)

el = ElectricalArchive(s)
j = EventJournal(s)

background_color = '#ffffff'
journal_id = 88
journal_id = 100004 #смена id журнала после обновления API

def load_data(start_date, end_date, selected, filtername = ''):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    start_date = datetime.datetime.combine(start_date, datetime.time(00, 00, 00))
    end_date = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))

    end = end_date.strftime("%Y-%m-%d %H:%M:%S")
    start = start_date.strftime("%Y-%m-%d %H:%M:%S")

    devs = pq_devices(s, ['obj-1'], 106)
    devs = devs.rename(columns={'name': 'common-device'})
    devs_list = devs['common-device'].tolist()
        #разбор выбранных в tree устройств
    selected = [x for x in selected if x in devs_list]
    if len(selected) == 0:
        return None

    df = j.get_data(journal_id, start, end, filters={'common-message': [filtername]})
    # df = j.get_data(journal_id, start, end, filters={'common-message': ['провал']})
    pass
    if df.empty:
        EMPTY_JOURNAL = True
        cols = ['dt', 'common-class', 'common-color', 'common-device', 'common-element',
                'common-level', 'common-message', 'common-number', 'common-type',
                'pq-duration', 'pq-magnitude', 'pq-reference', 'TBF', 'end', 'date']
        df[cols] = 0
        df['common-device'] = selected
        df['TBF'] = pd.NaT

    else:
        EMPTY_JOURNAL = False
        df['common-device'] = df['common-device'].map(lambda x: x.split('/')[-1])
        df = df.sort_index(ascending=True)
        df = df[df['common-device'].isin(selected)]
        if df.empty:
            EMPTY_JOURNAL = True

            # time between eventa by device
        df['TBF'] = df.reset_index().groupby('common-device')['dt'].diff().values
        # casting str to float
        df[['pq-duration', 'pq-magnitude', 'pq-reference']] = df[
            ['pq-duration', 'pq-magnitude', 'pq-reference']].replace("", 0).astype('float')
        # event_end
        df['end'] = df.index + pd.to_timedelta(df['pq-duration'], unit='s')
        # event_date
        df['date'] = df.index.date

    device_report = report_by_device(df, selected, start_date, end_date)
    common_report = report(df, selected, start_date, end_date)
    table = uptime_table(df, selected, start_date, end_date, EMPTY_JOURNAL)

    return [df.reset_index().to_json(), device_report.to_json(), common_report.to_json(), table.to_json()]


def update_table(df, ccolumns = None, tablename = ''):
    #df = df.reset_index()
    data = df.to_dict('records')
    if ccolumns is not None:
        columns=ccolumns
    else:
        columns = [{"name": i, "id": i, } for i in (df.columns)]

    return html.Div([
                html.Div(tablename, style={'font-size': '20px'}),
                dash_table.DataTable(data=data,
                                columns=columns,
                #export_format="xlsx",
                style_table={'overflow': 'auto'},
                style_cell={'font-size': 12, 'whiteSpace': 'pre-line', 'overflow': 'hidden', 'backgroundColor': "rgba(250,250,250,0.2)"},
                style_header={'backgroundColor': "#fafafa", 'fontWeight': 'bold'},
                style_data_conditional=[
                                    {
                                        "if": {"state": "selected"},  # 'active' | 'selected'
                                        "backgroundColor": "rgba(0, 116, 217, 0.3)",
                                        "border": "1px solid blue",
                                    },
                                ]
                                )
                    ])


def update_tree(checked, state=False):

    #device_list = s.devices_tree()
    #смена ветки API и структуры запроса/ответа в связи с обновлением
    device_list = s.get_data(s.host + '/sedmax/archive/channels_tree', {"treeType": "devices"})
    device_list = pd.DataFrame(device_list['tree'])
    device_list = device_list.rename(columns={'parentCode': 'parent', 'code': 'id'})

    devs = pq_devices(s, ['obj-1'], 106)
    devs = devs.rename(columns={'name': 'common-device'})

    # двухуровневая структура по дереву только до родителя
    nodes = []
    for i, row in devs.iterrows():
        # данные прибора
        node = []
        device_row = device_list[device_list['id'] == 'device-' + str(row['deviceId'])]
        name = device_row['name'].item()
        parent = device_row['parent'].item()
        node.append(name)

        # данные родителя прибора
        try:
            device_row = device_list[device_list['id'] == parent]
            parent_name = device_row['name'].item()
            node.append(parent_name)
        except:
            pass
        nodes.append(node)

    menu_list = []
    keys_list = []
    n = 0
    for node in nodes:
        if node[-1] not in keys_list:
            keys_list.append(node[-1])
            dev_dict = dict()
            dev_dict['title'] = node[-1]
            dev_dict['key'] = node[-1]
            dev_dict['children'] = [{'title': node[-2], 'key': node[-2]}]
            menu_list.append(dev_dict)
            n += 1
        else:
            ind = [i for i, e in enumerate(keys_list) if e == node[-1]][0]
            sub_n = len(menu_list[ind]['children'])
            menu_list[ind]['children'].append({'title': node[-2], 'key': str(ind) + '-' + str(sub_n)})

    if state:
        pass
    else:
        checked = devs['common-device'].tolist()

    tree_menu = html.Div(dash_treeview_antd.TreeView(
        id='tree_input',
        multiple=True,
        checkable=True,
        checked=checked,
        selected=[],
        expanded=keys_list,
        data={
            'title': 'Устройства ККЭ',
            'key': '0',
            'children': menu_list
            }
    ))
    return tree_menu

# Переменная с кодом дерева
tree = update_tree([], state=False)
#
common_table = html.Div(dash_table.DataTable(
                    id='common_table',
                    columns=[{'id': 'index', 'name': 'Характеристка'},
                             {'id': 'value', 'name': 'Значение'}],
                    style_cell={'font-size': 13, 'overflow': 'hidden', 'backgroundColor': "rgba(50,50,50,0.2)"},
                ), style={'padding': '5px'})
#
device_table = html.Div(dash_table.DataTable(
                    id='device_table',
                    columns=[{'id': 'Присоединение', 'name': 'Присоединение'},
                             {'id': 'Uptime', 'name': 'Время без сбоев, ч.'},
                             {'id': 'Uptime_percent', 'name': 'Время без сбоев, %'},
                             {'id': 'outage_time', 'name': 'Время сбоев, ч'},
                             {'id': 'outage_percent', 'name': 'Время сбоев, %'},
                             {'id': 'events', 'name': 'Количество сбоев'},
                             {'id': 'outage_min', 'name': 'Минимальое время сбоя, ч'},
                             {'id': 'outage_max', 'name': 'Максимальное время сбоя, ч'},
                             {'id': 'MTBF', 'name': 'Средняя наработка на отказ(MTBF)'},
                             {'id': 'MTTR', 'name': 'Среднее время восстановления(MTTR)'},
                             ],
                    style_cell={'font-size': 13, 'overflow': 'hidden', 'backgroundColor': "rgba(50,50,50,0.2)"},
                ), style={'padding': '5px'})

update_button = dbc.Button("Обновить", id="update_tree", n_clicks=0, className="ant-electro-btn-primary",
            style={'margin-right': '3px', 'font-family': 'sans-serif', 'font-size': '14px'}
           )

date_picker = html.Div([
    html.B(' Электроснабжение офиса. Анализ параметров ККЭ',
           style={'text-align': 'center', 'color': '#ffffff', 'font-size': 22, 'margin-left': '1%'}),
    html.Div([update_button,
    dcc.DatePickerRange(
            id='date-picker-range',
            initial_visible_month=datetime.datetime.now().date(),
            start_date=(datetime.datetime.now() - pd.Timedelta(days=30)).date(),
            end_date=datetime.datetime.now().date(),
            #month_format='MM/YYYY',
            )], style={'float': 'right', 'padding': '1px'})
            ],
            style={'margin-top': '1px', 'margin-bottom': '5px',
                    'backgroundColor': "grey", 'box-shadow': '0 0 2px 2px rgba(0,0,0,0.3)'}
        )


# tabs = [dbc.Tabs(
#             [
#                 dbc.Tab(label="Таблицы", tab_id="tables", tab_style={"marginLeft": "auto"}),
#                 dbc.Tab(label="Графики", tab_id="graphs"),
#             ],
#             id="tabs",
#             active_tab="tables",
#         ),
#         html.Div(id="content")]

# dbc.Row([
#     dbc.Col("Таблица обобщенных данных"),
#     dbc.Col("Таблица данных по устройствам")
# ]),


# Опции фильтрации журнала
values=['Провал напряжения', 'Повышение напряжения', 'Отклонение частоты', 'Доза фликера', 'Небаланс напряжения', 'Гармонические искажения']
options = []
for i in values:
    options.append({'label': i, 'value': i})
filter_kke = dcc.Dropdown(
    id='filter_kke',
    options=options,
    value='Провал напряжения',
    multi=False,
    clearable=False
    )
filter_content = html.Div([
    dbc.Row([
        dbc.Col("Выбор наименования сбоя", width=12),
    ], style={'font-size': 20, 'margin-left': '30px', 'flex-flow': 'row nowrap'}),
    dbc.Row([
        dbc.Col(filter_kke, width=12),
    ], style={'font-size': 14, 'margin-left': '30px', 'margin-right': '30px', 'margin-bottom': '10px', 'flex-flow': 'row nowrap'}),
    dbc.Row([])
])

tables_content = dbc.Container(dcc.Loading(type="circle",
    children=[
            dbc.Row([
                dbc.Col(html.Div(id="common_table"), width=3,
                        style={'padding': '5px', 'display': 'inline-table', 'backgroundColor': "#fafafa"
                                }),

                dbc.Col(html.Div(id="device_table"), width=9,
                        style={'padding': '5px','display': 'inline-table', 'backgroundColor': "#fafafa"
                                }),
                ], style={'padding': '5px', 'flex-flow': 'row no wrap'}),
            dbc.Row([
                dbc.Col(dcc.Graph(id='out_table', animate=False,
                        config= {'displayModeBar': False, 'locale': 'ru', 'staticPlot': True}), width=12),
                ], style={'padding': '5px', 'flex-flow': 'row nowrap'}),
        ]
    ), fluid=True, style={'background-color': background_color, 'overflow': 'auto'}
)

graphs_content = dbc.Container(
    [
        dbc.Row([
            dcc.Loading(type="circle",
                        children=[dcc.Graph(id='out_time_scatter', animate=False,
                                  config={'displaylogo': False, 'locale': 'ru'})]
                        )
        ], style={'padding': '5px'}),
    ], fluid=True, style = {'background-color': background_color, 'overflow': 'auto'}
)


tabs = [dbc.Tabs(
            [
                dbc.Tab(tables_content, label="Таблицы", tab_id="tables", tab_style={"marginLeft": "auto"}),
                dbc.Tab(graphs_content, label="Графики", tab_id="graphs")
            ],
            id="tabs",
            active_tab="tables",
            style={'margin': '5px'}
            ),
        html.Div(id="content")]


# Create an app layout
app.layout = html.Div(children=[
     html.Div(children=[
        dcc.Store(id='memory-output'),
        dbc.Row([SedmaxHeader(title='', logo='sedmax')]),
        dbc.Row([date_picker], style={'background-color': background_color})
     ], style={'position': 'fixed', 'width': '100%', 'z-index': '2'})
    ,
    html.Div(children=[
        dbc.Row([
            dbc.Col(html.Div(html.Div(id='tree', children=[tree]),
                             style={'box-shadow': '0 1px 4px 1px rgba(0,0,0,0.2)',
                                    'margin-top': '100px', 'overflowY': 'scroll',
                                    'height': 'calc(100vh - 98px)', 'margin-bottom': '120px'}),
                    style={'width': '250px'}),
            dbc.Col(html.Div([
                html.Div(filter_content,
                         style={'margin-top': '100px', 'margin-bottom': '7px', 'box-shadow': '0 1px 5px 1px rgba(0,0,0,0.2)'}),
                html.Div(tabs, style={'height': 'calc(100vh - 181px)', 'margin-bottom': '10px', 'overflowY': 'scroll', 'box-shadow': '0 1px 4px 1px rgba(0,0,0,0.2)'})
            ]), style={'min-width': 'calc(100% - 250px)'})

        ], style={'width': '100%', 'flex-flow': 'row nowrap'})
    ], style={'position': 'fixed', 'width': '100%', 'z-index': '1', 'hight': 'calc(100% - 100px)'}),
    ])

@app.callback(Output(component_id='tree', component_property='children'),
              [Input("update_tree", "n_clicks"),
               State('tree_input', 'checked')], prevent_initial_call=True)
def update(n, checked):
    tree = update_tree(checked, state=True)
    return tree


@app.callback([Output(component_id='memory-output', component_property='data')],
              [Input('date-picker-range', 'start_date'),
               Input('date-picker-range', 'end_date'),
               Input('tree_input', 'checked'),
               Input(component_id='filter_kke', component_property='value')]
              )
def update_global_var(start_date, end_date, selected, filtername):
    df = load_data(start_date, end_date, selected, filtername)
    return [df]


# @app.callback(Output("content", "children"), [Input("tabs", "active_tab")])
# def switch_tab(at):
#     if at == "tables":
#         return tables_content
#     elif at == "graphs":
#         return graphs_content


@app.callback(
    [Output(component_id='common_table', component_property='children'),
    Output(component_id='device_table', component_property='children'),
    Output(component_id='out_table', component_property='figure'),
    ],
    [Input(component_id='memory-output', component_property='data')]
 )


def show_report(data):

    if type(data) is list:
        #графики
        df = pd.read_json(data[0]).set_index('dt')
        df.index = pd.to_datetime(df.index, unit='ms')
        table = pd.read_json(data[3])

        heatmap = out_table(table)

        #таблицы
        columns = [{'id': 'Присоединение', 'name': 'Наименование устройства'},
                {'id': 'Uptime', 'name': 'Время без сбоев, сек.'},
                {'id': 'Uptime_percent', 'name': 'Время без сбоев, %'},
                {'id': 'outage_time', 'name': 'Время сбоев, сек.'},
                {'id': 'outage_percent', 'name': 'Время сбоев, %'},
                {'id': 'events', 'name': 'Количество событий'},
                {'id': 'outage_min', 'name': 'Минимальное время сбоя, сек.'},
                {'id': 'outage_max', 'name': 'Максимальное время сбоя, сек.'},
                {'id': 'MTBF', 'name': 'Средняя наработка на отказ (MTBF)'},
                {'id': 'MTTR', 'name': 'Среднее время восстановления (MTTR), сек.'},
                ]


        device_report = update_table(pd.read_json(data[1]), columns,"Общие данные")

        columns = [{'id': 'Характеристика', 'name': 'Характеристка'},
                   {'id': 'Значение', 'name': 'Значение'}]
        common_report = update_table(pd.read_json(data[2]), columns, "Данные по устройствам")

        return [common_report, device_report, heatmap]
    else:
        return [html.Div(), html.Div(), empty_plot()]

@app.callback(
    [
    Output(component_id='out_time_scatter', component_property='figure'),
    ],
    [Input(component_id='memory-output', component_property='data')],
 )
def show_report(data):

    if type(data) is list:
        #графики
        df = pd.read_json(data[0]).set_index('dt')
        df.index = pd.to_datetime(df.index, unit='ms')

        if df['pq-duration'].notnull().values.any():
            scatter = out_time_scatter(df)
        else:
            scatter = empty_plot()
    else:
        scatter = empty_plot()
    return [scatter]
