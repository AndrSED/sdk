from enum import Enum

SANKEY_DATABASE = 'sankey_base.db'

# colors = {
#     'grid': "#b9b9b9",
#     'graph_font': "#000000",
#     'plot_area': "#ffffff",
#     'plot_background': "#fafafa",
#     'active_link': 'rgba(200,200,200,0.7)',
#     'disabled_link': 'rgba(250,100,100,0.7)',
#     'node': 'rgba(200,200,200,0.7)',
# }


class SankeyColor(Enum):
    GRAPH_FONT = "#000000"
    PLOT_BACKGROUND = "#fafafa"
