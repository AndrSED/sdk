import time
import aiohttp

import sankey.prepare_data_new as snk
from sdk import SedmaxHeader, Sedmax, ElectricalArchive

s = Sedmax('https://demo.sedmax.ru')

req = {'channels': ['el-dev-101-ea_imp-30m', 'el-dev-102-ea_imp-30m'],
       'begin': '2022-02-15 05:00:00', 'end': '2023-03-03 05:00:00'}

username = 'demo'  # os.environ['SEDMAX_USERNAME']
password = 'demo'  # os.environ['SEDMAX_PASSWORD']
s.login(username, password)


resp = snk.load_data(s, '2023-03-01 00:30:00', '2023-03-02 00:30:00')
print(s.node.keys())
print(resp)
