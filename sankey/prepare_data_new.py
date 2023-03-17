import numpy as np
from pandas import DataFrame
import plotly.graph_objects as go

from sdk import Sedmax

colors = {
    'grid': "#b9b9b9",
    'graph_font': "#000000",
    'plot_area': "#ffffff",
    'plot_background': "#fafafa",
    'active_link': 'rgba(200,200,200,0.7)',
    'disabled_link': 'rgba(250,100,100,0.7)',
    'node': 'rgba(200,200,200,0.7)',
}


# generate color
def generate_random_color(size=3):
    r, g, b = np.random.randint(low=10, high=255, size=size)
    return f'rgba({r}, {g}, {b}, 0.2)'


def prepare_arch_request(devices, start_time, end_time) -> dict:
    # print(devices)
    channels_recive = ['el-dev-' + str(dev) + '-ea_imp-30m' for dev in devices]
    channels_trans = ['el-dev-' + str(dev) + '-ea_exp-30m' for dev in devices]
    req = {
        "channels": channels_recive + channels_trans,
        # "channels": channels_recive,
        "begin": start_time,
        "end": end_time,
    }
    return req


def getting_arch_from_api_for_sankey(s: Sedmax, req) -> dict:
    sum_energy = {}
    url = s.host + '/sedmax/archive_webapi/archive'
    raw_data = s.get_data(url, req)
    for chanel in raw_data:
        dev, _, side = chanel['channel'].lstrip('el-dev-').rstrip('-30m').partition('-')
        dev = int(dev)
        total = sum([x['v'] for x in chanel['data']])
        # print(f'{dev=} {total=} {side=}')
        if sum_energy.get(dev):
            if side == 'ea_imp':
                sum_energy[dev] = sum_energy[dev] + total
            elif side == 'ea_exp':
                sum_energy[dev] = sum_energy[dev] - total
            else:
                print(f'Ошибка приёма ')
        else:
            if side == 'ea_imp':
                sum_energy[dev] = total
            elif side == 'ea_exp':
                sum_energy[dev] = -(total)
            else:
                print(f'Ошибка приёма ')
    print(f'{sum_energy=}')
    return sum_energy


def prepare_label(s: Sedmax) -> list:
    return [key for key in s.node]


def cleaning_data(df: DataFrame) -> DataFrame:
    for row in df.itertuples():
        if row[4] == 0:
            df.at[row[0], 'sum_energy'] = 0.01
        elif row[4] < 0:
            val = row[4]
            start = row[2]
            end = row[3]
            df.at[row[0], 'sum_energy'] = abs(val)
            df.at[row[0], 'start_node'] = end
            df.at[row[0], 'end_node'] = start
    return df


def prepare_source_target(label: list, s: Sedmax, df: DataFrame):
    label_index = [s.node[x] for x in label]
    # print(label_index)
    source = []
    target = []
    for row in df.itertuples():
        source.append(label_index.index(row[2]) + 1)
        target.append(label_index.index(row[3]) + 1)
    return source, target


def generate_link_color(s: Sedmax, source: list) -> list:
    return [s.node_color[i] for i in source]


def load_data(s, start_date, end_date):
    labels = prepare_label(s)
    # print(labels)
    request = prepare_arch_request(s.channel.index.tolist(), start_date, end_date)
    # print(request)
    arch_data = getting_arch_from_api_for_sankey(s, request)
    data_df = s.channel.copy()
    print('чистая дата', data_df)
    data_df['sum_energy'] = data_df.index.map(arch_data)
    print('присоединение энергии', data_df)
    data_df = cleaning_data(data_df)
    print('после очистки', data_df)
    value = data_df['sum_energy'].tolist()
    source, target = prepare_source_target(labels, s, data_df)
    link_colors = generate_link_color(s, source)
    print(f'{source=}')
    print(f'{target=}')
    print(f'{value=}')

    return [{"source": source, "target": target, "value": value, "labels": labels, "link_colors": link_colors,
             "sourse_colors": s.node_color}]


def sankey_plot(data):
    fig = go.Figure(go.Sankey(
        valuesuffix=" кВтч",
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=data["labels"],
            color=colors['node'],
            # color=data["sourse_colors"]
            # x= [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            # y= [0.2, 0.1, 0.5, 0.7, 0.3, 0.5],
            # color = "blue"
        ),
        link=dict(
            source=data["source"],  # indices correspond to labels, eg A1, A2, A1, B1, ...
            target=data["target"],
            value=data["value"],
            color=data["link_colors"],
        )))
    fig.update_layout(height=700,
                      font_color=colors['graph_font'],
                      font_size=10,
                      # title_text='Электроснабжение офиса. Активная электроэнергия',
                      # plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      # margin=dict(l=20, r=20, b=30, t=30, pad=1),
                      )

    return fig
