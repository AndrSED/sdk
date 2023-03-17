import sqlite3 as sl
import pandas as pd
from contextlib import closing


from sdk import SedmaxHeader, Sedmax, ElectricalArchive

s = Sedmax('https://demo.sedmax.ru')

username = 'demo'  # os.environ['SEDMAX_USERNAME']
password = 'demo'  # os.environ['SEDMAX_PASSWORD']
s.login(username, password)

# con = sl.connect('sankey_base.db')

# base_df = pd.read_sql('''SELECT * FROM sankey_config''', con)


req = {'channels': ['el-dev-100-ea_imp-30m', 'el-dev-101-ea_imp-30m', 'el-dev-102-ea_imp-30m', 'el-dev-103-ea_imp-30m', 'el-dev-104-ea_imp-30m', 'el-dev-105-ea_imp-30m', 'el-dev-106-ea_imp-30m', 'el-dev-107-ea_imp-30m', 'el-dev-108-ea_imp-30m', 'el-dev-109-ea_imp-30m', 'el-dev-110-ea_imp-30m', 'el-dev-111-ea_imp-30m', 'el-dev-112-ea_imp-30m', 'el-dev-113-ea_imp-30m', 'el-dev-114-ea_imp-30m', 'el-dev-115-ea_imp-30m', 'el-dev-100-ea_exp-30m', 'el-dev-101-ea_exp-30m', 'el-dev-102-ea_exp-30m', 'el-dev-103-ea_exp-30m', 'el-dev-104-ea_exp-30m', 'el-dev-105-ea_exp-30m', 'el-dev-106-ea_exp-30m', 'el-dev-107-ea_exp-30m', 'el-dev-108-ea_exp-30m', 'el-dev-109-ea_exp-30m', 'el-dev-110-ea_exp-30m', 'el-dev-111-ea_exp-30m', 'el-dev-112-ea_exp-30m', 'el-dev-113-ea_exp-30m', 'el-dev-114-ea_exp-30m', 'el-dev-115-ea_exp-30m'], 'begin': '2023-03-01 05:00:00', 'end': '2023-03-03 05:00:00'}


url = s.host + '/sedmax/archive_webapi/archive'
raw_data = s.get_data(url, req)
print(raw_data)

def prepaire_arch_request(devices, start_time, end_time) -> dict:
    channels = ['el-dev-' + str(dev) + '-ea_imp-30m' for dev in devices]
    return {
        "channels": channels,
        "begin": start_time,
        "end": end_time,
    }


def getting_arch_from_api(s, request):
    final = {}
    url = s.host + '/sedmax/archive_webapi/archive'
    raw_data = s.get_data(url, request)
    for chanel in raw_data:
        total = sum([x['v'] for x in chanel['data']])
        final[chanel['channel']] = total
    return final


def prepaire_nodes():
    pass


# print(base_df)
# print(base_df)
# dct = []
# for index, row in base_df.iterrows():
#     t = row.values.tolist()
#     dct.append({t[2]: {'sed_id': t[1], 'parents': t[3], 'type': 'el-dev-' + str(t[1]) + '-ea_imp-30m'}})
# #
# print(dct)
# nodes = base_df['name'].values.tolist()
# parents = base_df['parents'].values.tolist()
# print(nodes)
# print(parents)
# # print(df['sed_id'].values.tolist())
# # device_list = df.values.tolist()
# device_list = ["110"]
# prepaired_request = prepaire_arch_request(device_list, "2023-03-01 00:00:00", "2023-03-01 23:59:59")
# arch_df = getting_arch_from_api(s, dct)
# print(arch_df)
# for i, val in enumerate(nodes):

# l = [{'dt': '2023-03-01 00:00:00', 'v': 0.651}, {'dt': '2023-03-01 00:30:00', 'v': 5.651}]
# total = [i['v']for i in l]
# print(total)
