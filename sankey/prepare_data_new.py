import numpy as np
import plotly.graph_objects as go
from pandas import DataFrame

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
    channels_recive = ['el-dev-' + str(dev) + '-ea_imp-30m' for dev in devices]
    # channels_trans = ['el-dev-' + str(dev) + '-ea_exp-30m' for dev in devices]
    return {
        # "channels": channels_recive + channels_trans,
        "channels": channels_recive,
        "begin": start_time,
        "end": end_time,
    }


def getting_arch_from_api_for_sankey(s: Sedmax, req) -> dict:
    sum_energy = {}
    url = s.host + '/sedmax/archive_webapi/archive'
    raw_data = s.get_data(url, req)
    for chanel in raw_data:
        dev, _, side = chanel['channel'].lstrip('el-dev-').rstrip('-30m').partition('-')
        total = sum([x['v'] for x in chanel['data']])
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


def prepare_source_target_value(label: list, s: Sedmax, df: DataFrame):
    label_index = [s.node[x] for x in label]
    # print(label_index)
    source = []
    target = []
    value = df['sum_energy'].tolist()
    for row in df.itertuples():
        source.append(label_index.index(row[2]))
        target.append(label_index.index(row[3]))
    return source, target, value


def geberate_link_color() -> list:
    pass


def load_data(s, start_date, end_date):
    sourse_colors = []
    link_colors = []    # Доделать цвет линков
    labels = prepare_label(s)
    request = prepare_arch_request([s.channel.index], start_date, end_date)
    print(request)
    # arch_data = getting_arch_from_api_for_sankey(s, request)
    # data_df = s.channel.copy()
    # data_df['sum_energy'] = arch_data
    # data_df = cleaning_data(data_df)
    # source, target, value = prepare_source_target_value(labels, s, data_df)
    # return [{"source": source, "target": target, "value": value, "labels": labels, "link_colors": link_colors,
    #          "sourse_colors": sourse_colors}]


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


s = Sedmax('https://demo.sedmax.ru')

username = 'demo'  # os.environ['SEDMAX_USERNAME']
password = 'demo'  # os.environ['SEDMAX_PASSWORD']
s.login(username, password)
load_data(s, "2023-03-01 00:00:00", "2023-03-02 00:00:00")