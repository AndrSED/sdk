import json
import requests
import pandas as pd
import sqlite3
import numpy as np
from contextlib import closing

from settings import SANKEY_DATABASE


class Sedmax:
    __node_visibility = 1
    __link_visibility = 0.2

    def __init__(self, host='http://127.0.0.1'):
        self.host = host
        self.token = None
        self.username = None
        self.password = None
        self.db = SANKEY_DATABASE
        self.node = self.getting_nodes(self.db)
        self.channel = self.getting_channel(self.db)
        self.node_color = self.prepare_node_color(self.db)
        self.link_color = self.prepare_link_color(self.node_color)

    @classmethod
    def getting_nodes(cls, db):
        with closing(sqlite3.connect(db)) as connection:
            cursor = connection.cursor()
            cursor.execute("""select node_name, id from node """)
            node = dict(cursor.fetchall())
            # print(node)
            return node

    @classmethod
    def getting_channel(cls, db):
        with closing(sqlite3.connect(db)) as connection:
            channel_df = pd.read_sql('''SELECT sed_id, channel_name, start_node, end_node FROM channel''', connection)
            channel_df.set_index('sed_id', inplace=True)
            # print(channel_df)
            return channel_df

    @classmethod
    def prepare_node_color(cls, db):
        with closing(sqlite3.connect(db)) as connection:
            cursor = connection.cursor()
            cursor.execute("""select node_color from node """)
            node_raw = list(cursor.fetchall())
            node_color = ['rgba(' + color[0] + ',' + str(cls.__node_visibility) + ')' for color in node_raw]
            # print(node_color)
            return node_color

    @classmethod
    def getting_node_color(cls, db):
        with closing(sqlite3.connect(db)) as connection:
            node_color_df = pd.read_sql('''select node_color from node''', connection)
            # print('ноды', node_color_df['node_color'].tolist())
            return node_color_df['node_color'].tolist()

    @classmethod
    def prepare_link_color(cls, node_color: list[str]):
        link_colors = [color.rpartition(',')[0] + ',' + str(cls.__link_visibility) + ')' for color in node_color]
        # print(link_colors)
        return link_colors

    # @classmethod
    # def getting_link_color(cls, db):
    #     with closing(sqlite3.connect(db)) as connection:
    #         link_color_df = pd.read_sql('''select link_color from node''', connection)
    #         print(link_color_df['link_color'].tolist())
    #         return link_color_df['link_color'].tolist()

    # @classmethod
    # def generate_random_color(cls, size=3):
    #     r, g, b = np.random.randint(low=10, high=255, size=size)
    #     return f'rgba({r}, {g}, {b}, 0.2)'

    def login(self, username, password):
        r = requests.post(
            self.host + '/sedmax/auth/login',
            data=json.dumps({'Login': username, 'Password': password})
        )

        if r.status_code == 200:
            self.token = r.cookies.get_dict()["jwt"]
            self.username = username
            self.password = password
        else:
            raise Exception(f'Status code: {r.status_code}. {r.json()["message"]}')

    def update_token(self):
        if self.username is not None and self.password is not None:
            r = requests.post(
                self.host + '/sedmax/auth/login',
                data=json.dumps({'Login': self.username, 'Password': self.password})
            )
            if r.status_code == 200:
                self.token = r.cookies.get_dict()["jwt"]
            else:
                raise Exception(f'Status code: {r.status_code}, message: {r.json()["message"]}')
        else:
            raise Exception(f'Need to login first. Use login("username", "password") method.')

    def get_token(self):
        return self.token

    def get_url(self):
        return self.host

    def get_data(self, url, request):
        # print(f'{url=}')
        # print(f'{request=}')
        r = requests.post(
            url,
            json=request,
            cookies={'jwt': self.token}
        )

        if r.status_code == 200:
            return r.json()
        elif r.status_code == 401 or r.status_code == 403:
            self.update_token()
            new_r = requests.post(
                url,
                json=request,
                cookies={'jwt': self.token}
            )
            if new_r.status_code == 200:
                return new_r.json()
            else:
                raise Exception(f'Status code: {r.status_code}, message: {r.json()["message"]}')
        else:
            raise Exception(f'Status code: {r.status_code}, message: {r.json()["message"]}')

    def categories(self):
        url = self.host + '/sedmax/web/archive/categories'
        request = {}
        r = self.get_data(url, request)
        return r['categories']

    def devices_tree(self):
        url = self.host + '/sedmax/web/archive/devices_tree'
        df = pd.DataFrame()
        for category in ['electro', 'energy', 'emission']:
            data = self.get_data(url, {'category': category})
            data = pd.DataFrame(data['treeObject'])
            data['category'] = category
            df = pd.concat([df, data]).reset_index(drop=True)

        return df

    def devices_list(self, nodes):
        if type(nodes) is not list:
            raise Exception(f'Nodes expected to be a "list" type, got {type(nodes)} instead')

        url = self.host + '/sedmax/devices_configurator/devices/list'
        request = {
            'limit': 0,
            'nodes': nodes,
            'offset': 0
        }
        r = self.get_data(url, request)

        return pd.DataFrame(r['devices'])

    def ti_list(self, nodes):
        if type(nodes) is not list:
            raise Exception(f'Nodes expected to be a "list" type, got {type(nodes)} instead')

        url = self.host + '/sedmax/devices_configurator/ti/list'
        request = {
            'nodes': nodes,
        }
        r = self.get_data(url, request)

        return pd.DataFrame(r['ti'])

# s.electro.get_electro_data([{'device': 101, 'channel': "ea_imp"}],period="30min",begin='2021-01-24',end='2021-01-26')
# s.electro.get_data(["dev-101_ea_imp"],period=["30min"],begin='2021-01-24',end='2021-01-26')
