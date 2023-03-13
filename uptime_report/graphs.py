import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff

import matplotlib.colors as mcolors

colors = {
    'grid': "#b9b9b9",
    'graph_font': "#000000",
    'plot_area': "#ffffff",
    'plot_background': "#fafafa",
}

def out_time_scatter(df):
    df = df[df.index.notnull()]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.2, 0.25])

    #device_colors = ['rgb(220,20,60)', 'rgb(204,204,0)', 'rgb(20,60,220)']
    device_colors = list(mcolors.TABLEAU_COLORS.values())

    for i, device in enumerate(df['common-device'].unique()):

        color_id = i - len(device_colors) if i >= len(device_colors) else i

        data = df[df['common-device'] == device]
        summary = data.groupby(data.index.date).sum()

        fig.add_trace(go.Scatter(x=data.index, y=data['pq-duration'], name=device, opacity=0.6,
            legendgroup=f'group{i + 1}', showlegend=False,
                mode='markers', marker=dict(size=12, color=device_colors[color_id], line=dict(width=1, color='white')),
                                 ), row=1, col=1)

        fig.add_trace(go.Bar(x=summary.index, y=summary['pq-duration'],
                             name=device, marker_color=device_colors[color_id], legendgroup=f'group{i + 1}'), row=2, col=1)

    fig.update_layout(height=800,
                      xaxis=dict(gridcolor=colors['grid'], dtick = pd.to_timedelta(1, unit="D"),
                                 showline=True, linewidth=1, linecolor=colors['grid'], mirror=True),
                      xaxis2=dict(gridcolor=colors['grid'], dtick = pd.to_timedelta(1, unit="D"),
                                 showline=True, linewidth=1, linecolor=colors['grid'], mirror=True),
                      yaxis=dict(gridcolor=colors['grid'], zeroline=False,
                                 showline=True, linewidth=1, linecolor=colors['grid'], mirror=True),
                      yaxis2=dict(gridcolor=colors['grid'], zeroline=False,
                                 showline=True, linewidth=1, linecolor=colors['grid'], mirror=True),
                      xaxis_range=(df.date.min()-datetime.timedelta(days=1), df.date.max()+datetime.timedelta(days=1)),
                      xaxis2_range=(df.date.min() - datetime.timedelta(days=1), df.date.max() + datetime.timedelta(days=1)),
                      yaxis1_title="Продолжительность, c",
                      yaxis2_title="Общее время, c",
                      font_color=colors['graph_font'],
                      title_text='Продолжительность сбоев',
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      margin=dict(l=20, r=20, b=30, t=80, pad=1),
                      )

    fig.update_yaxes(
        title_standoff=3,
        title_font={"size": 12})

    return fig


def out_table(df):
    df = df.fillna(0).astype(int)

    x = [x.strftime("%b, %d") for x in df.columns.to_list()]
    y = df.index.to_list()
    z_text = [list(df.iloc[i].values) for i in range(len(y))]
    z = np.array(z_text).clip(0, 10)

    colorscale = [[0, 'rgb(0,180,0)'],
                  [0.1, 'rgb(255, 190, 0)'],
                  [0.25, 'rgb(255, 128, 0)'],
                  [1, 'rgb(255, 0, 0)']]

    fig = ff.create_annotated_heatmap(z, x=x, y=y, colorscale=colorscale, xgap=1, ygap=1,
                                      annotation_text=z_text, text=z_text, hoverinfo='text')

    height = max(85 * len(df), 250)
    fig.update_layout(height=height,
                      xaxis=dict(showgrid=False, side='top'),
                      yaxis=dict(showgrid=False),
                      font_color=colors['graph_font'],
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      title_text='Тепловая карта сбоев',
                      titlefont=dict(size=20),
                      margin=dict(l=20, r=20, b=30, t=100, pad=1)
                      )
    return fig
