import pandas as pd
import numpy as np

def pq_devices(s, nodes, protocol_Id):
    df = s.devices_list(nodes)
    if df.empty:
        return df
    df['protocols'] = df['protocols'].apply(lambda x: [(k, v) for d in x for k, v in d.items()])
    df['PQ'] = df['protocols'].apply(lambda x: True if ('protocolId', protocol_Id) in x else False)
    df_pq = df[df['PQ']]
    return df_pq


def report_by_device(df, devs_list, start, end):

    total_time = (end - start).total_seconds()

    # Шаблон отчета по утройствам
    report_template = pd.DataFrame({'Присоединение': devs_list})
    report_template[['Uptime', 'Uptime_percent', 'outage_time', 'outage_percent']] = total_time, 100, 0, 0
    report_template[['events', 'outage_min', 'outage_max', 'MTBF', 'MTTR']] = 0, np.NaN, np.NaN, pd.NaT, np.NaN

    report_template = report_template.reset_index().drop('index', axis=1)

    def features(df):
        outage_time = df.groupby('common-device')['pq-duration'].sum().item()
        events = df.groupby('common-device')['common-number'].count().item()
        outage_min = np.round(df.groupby('common-device')['pq-duration'].min().item(), 2)
        outage_max = np.round(df.groupby('common-device')['pq-duration'].max().item(), 2)
        MTBF = str(df.groupby('common-device')['TBF'].mean().dt.round(freq='S').item()).replace('days', 'д')  # seconds
        MTTR = df.groupby('common-device')['pq-duration'].mean().item()

        return outage_time, events, outage_min, outage_max, MTBF, MTTR

    def calc_features(df):
        df['Uptime'] = total_time - df['outage_time']
        df['Uptime_percent'] = 100 * df['Uptime'] / total_time
        df['outage_percent'] = 100 * df['outage_time'] / total_time
        return df

    for i, row in report_template.iterrows():
        obj = row['Присоединение']
        subset = df[df['common-device'] == obj]
        if len(subset) > 0:
            report_template.loc[i, ['outage_time', 'events', 'outage_min', 'outage_max', 'MTBF', 'MTTR']] = features(
                subset)

    report_template = calc_features(report_template).round(3)
    report_template[['outage_percent', 'Uptime_percent']] = report_template[['outage_percent', 'Uptime_percent']].astype(str)
    return report_template


def report(df, device_list, start, end):

    data = df[df['common-device'].isin(device_list)]

    total_time = (end - start).total_seconds()
    outage_time = np.round(data["pq-duration"].sum(), 3)

    total = pd.DataFrame.from_dict(
        {'Выбранный период анализа': start.strftime("%d %b %Y") + " - " + end.strftime("%d %b %Y"),
         'Секунд в выбранном периоде': f'{int(total_time)}, сек',
         # 'Outage': f'{outage_time}, сек',
         'Общее время сбоев': f'{outage_time}, сек',
         # 'Uptime': f'{total_time - outage_time}, сек',
         'Общее время без сбоев': f'{total_time - outage_time}, сек',
         'Количество событий': data["common-number"].count(),
         'Количество устройств': len(device_list),
         'Общая наработка на отказ (MTBF Total):': str(data["TBF"].mean().round(freq="T")),
         'Общее среднее время восстановления (MTTR Total):': f'{np.round(data["pq-duration"].mean(), 3)}, сек'
         },
        orient='Index')
    total = total.reset_index()
    total = total.rename(columns={'index':'Характеристика', 0:'Значение'})

    return total


def uptime_table(df, devs_list, start, end, EMPTY_JOURNAL):
    # Шаблон для таблицы отказов

    days = pd.date_range(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), freq='D')
    outer_template = pd.DataFrame({'date': days.date})
    for dev in devs_list:
        outer_template[dev] = np.NaN

    if EMPTY_JOURNAL:
        outer_template = outer_template.set_index('date').transpose().fillna(0)
        outer_template = outer_template.astype('int')
    else:
        # События из журнала
        events = df.groupby(['common-device', 'date']).count().reset_index()
        data = outer_template.merge(events[['common-device', 'date', 'common-number']], how='left')
        data = data.pivot(index='date', columns='common-device')['common-number']

        # Добавить события в шаблон
        for dev in data:
            if dev in outer_template.columns:
                outer_template[dev] = data[dev].to_numpy()

        outer_template = outer_template.set_index('date').transpose().fillna(0)
        outer_template = outer_template.astype('int')

    return outer_template

def empty_plot():
    return {
        "layout": {
            "xaxis": {
                "visible": False
            },
            "yaxis": {
                "visible": False
            },
            "annotations": [
                {
                    "text": "Отсутствуют данные для отображения",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 28,
                        "color": "gray"
                    }
                }
            ]
        }
    }

