# %%
# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output

from toolbox import work_load, countries, trades

# %%
app = Dash(__name__)


# %%
# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
# df = pd.DataFrame({
#     "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
#     "Amount": [4, 1, 2, 2, 4, 5],
#     "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
# })

# fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

def generate_table(dataframe, max_rows=20):

    def _list_to_str(maybe_list):
        if isinstance(maybe_list, list):
            return ', '.join(maybe_list)
        return maybe_list

    return html.Table(
        children=[
            html.Thead(
                html.Tr([html.Th(col) for col in dataframe.columns])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(_list_to_str(dataframe.iloc[i][col])) for col in dataframe.columns
                ]) for i in range(min(len(dataframe), max_rows))
            ])
        ],
        className='fl-table'
    )


running_data = work_load(countries[0], trades[0])

fig = running_data['fig']
table = generate_table(running_data['df'])


# %%
app.layout = html.Div(children=[
    html.Div(children=[
        html.H1('''Country's trade partner''')
    ]),

    html.Div(
        children=[
            html.Label('Select country'),
            dcc.Dropdown(id='dropdown-1', options=countries,
                         value=countries[0]),

            html.Br(),
            html.Label('Select trade'),
            dcc.RadioItems(id='radioitems-1', options=trades, value=trades[0]),
        ],
        style={'padding': 10, 'flex': 1}
    ),

    dcc.Graph(
        id='graph-1',
        figure=running_data['fig']
    ),

    html.Div(
        id='table-div-1',
        children=[generate_table(running_data['df'])],
    )
])

# %%


@app.callback(
    [Output('graph-1', 'figure'), Output('table-div-1', 'children')],
    Input('dropdown-1', 'value'),
    Input('radioitems-1', 'value')
)
def update(country, trade):
    running_data = work_load(country, trade)

    fig = running_data['fig']
    table = generate_table(running_data['df'])

    return fig, [table]


# %%
if __name__ == '__main__':
    app.run_server(debug=True)
