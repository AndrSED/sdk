import sqlite3
from contextlib import closing

db = 'sankey_base.db'


with closing(sqlite3.connect(db)) as connection:
    cursor = connection.cursor()
    cursor.execute("""select node_name, id from node """)
    node = dict(cursor.fetchall())
    print(node)