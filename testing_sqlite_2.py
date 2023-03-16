import sqlite3
from contextlib import closing

from sdk import SedmaxHeader, Sedmax, ElectricalArchive

s = Sedmax('https://demo.sedmax.ru')

username = 'demo'  # os.environ['SEDMAX_USERNAME']
password = 'demo'  # os.environ['SEDMAX_PASSWORD']
s.login(username, password)

print(s.node)
# print(s.channel)
label_index = [s.node[x] for x in label]
revers_label = {val: key for key, val in s.node.items()}
print(revers_label)
