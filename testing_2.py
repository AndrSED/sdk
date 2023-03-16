from pandas import DataFrame
from sdk import SedmaxHeader, Sedmax, ElectricalArchive

test_response = {
    'el-dev-101-ea_imp-30m': 100.123,
    'el-dev-101-ea_exp-30m': 200.123,
    'el-dev-102-ea_imp-30m': 300.123,
    'el-dev-102-ea_exp-30m': 400.123,
}

ttt = {
    100: 1.123,
    101: -100.123,
    102: 200.123,
    103: -300.123,
    104: 400.123,
    105: 500.123,
    106: 600.123,
    107: 700.123,
    108: -800.123,
    109: 900.123,
    110: 450.123,
    111: -4560.123,
    112: 459800.123,
    113: 1100.123,
    114: 12340.123,
    115: 46545234.123,
}


def prepaire_arch_request(devices, start_time, end_time) -> dict:
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


def prepaire_label(s: Sedmax) -> list:
    return [key for key in s.node]


def cleaning_data(df: DataFrame) -> DataFrame:
    for row in df.itertuples():
        if row[4] == 0:
            new_fr.at[row[0], 'sum_energy'] = 0.01
        elif row[4] < 0:
            val = row[4]
            start = row[2]
            end = row[3]
            new_fr.at[row[0], 'sum_energy'] = abs(val)
            new_fr.at[row[0], 'start_node'] = end
            new_fr.at[row[0], 'end_node'] = start
    return df


def prepaire_source_target_value(label: list, s: Sedmax, df: DataFrame):
    label_index = [s.node[x] for x in label]
    # print(label_index)
    source = []
    target = []
    value = df['sum_energy'].tolist()
    for row in df.itertuples():
        source.append(label_index.index(row[2]))
        target.append(label_index.index(row[3]))
    return source, target, value


s = Sedmax('https://demo.sedmax.ru')

username = 'demo'  # os.environ['SEDMAX_USERNAME']
password = 'demo'  # os.environ['SEDMAX_PASSWORD']
s.login(username, password)
label = prepaire_label(s)
print(label)
# print(prepaire_label(s))

# print(s.channel)
#
new_fr = s.channel.copy()
new_fr['sum_energy'] = ttt
print(new_fr)
cleaning_data(new_fr)
print(new_fr)
source, target, value = prepaire_source_target_value(label, s, new_fr)
print(source)
print(target)
print(value)
# print(s.channel.index[1])
# request = prepaire_arch_request([s.channel.index[1]], "2023-03-01 00:00:00", "2023-03-01 23:59:59")
# print(request)
# print(getting_arch_from_api_for_sankey(s, request))
# print(s.node)
# print(s.channel)
