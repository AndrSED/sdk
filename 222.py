import sankey.prepare_data_new as snk
from sdk import SedmaxHeader, Sedmax, ElectricalArchive

s = Sedmax('https://demo.sedmax.ru')

username = 'demo'  # os.environ['SEDMAX_USERNAME']
password = 'demo'  # os.environ['SEDMAX_PASSWORD']
s.login(username, password)
snk.load_data(s,'2023-03-01 00:30:00', '2023-03-02 00:30:00')
# request = snk.prepare_arch_request(s.channel.index.tolist(), '2023-03-01 00:30:00', '2023-03-02 00:30:00')
# print('тута', request)

