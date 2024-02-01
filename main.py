import pandas as pd
import numpy as np
from collections import Counter
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import dash_table

# App initialization
app = dash.Dash(__name__)


#Preprocessing
def preprocess(data_total, data_capita, data_sector):
    sectors = list(set(data_sector.Sector))

     # Remove all countries that are not in data_capita
    countries = set(data_capita.index) # Countries that will be used
    data_total = data_total.drop(set(data_total.index) - countries)
    data_sector = data_sector.drop(set(data_sector.index) - countries)

    # Remove sector if 20 % of information unkown
    data_sector_clean = data_sector.loc[np.sum(data_sector[years].isna(), axis = 1) < int(data_sector[years].shape[1] * 0.2)]

    #since total value and sum of all sectors of a country is close to 0, fill the missing data with 0. Prove of it in the COLLAB
    data_sector_clean = data_sector_clean.fillna(0)
    return data_total, data_capita, data_sector_clean

# Line graph update
@app.callback(
    Output('graph-placeholder', 'figure'),
    [Input('my-dmc-radio-item', 'value')]
)
def update_graph_line(col_chosen):
    fig = px.line(data_total.transpose().loc[years], x=years, y=col_chosen)
    for i in sectors:
      np.where(data_sector.Sector == i)
    fig.update_layout(xaxis_title='Year', yaxis_title='Mt CO2', title=col_chosen)

    return fig

@app.callback(
    Output('pie-chart', 'figure'),
    [Input('sector-slider', 'value')]
)
def update_pie_chart(year):
    fig = px.pie(names=sectors, values=vals[:,years.index(year)], hole=0.5
    , title=f"CO2 emission by sector for {year}") 
    return fig

#Read csv
name = "data/CO2.xlsx"
data_total = pd.read_excel(name, sheet_name='fossil_CO2_totals_by_country').set_index("ISOcode")
data_capita = pd.read_excel(name, sheet_name='fossil_CO2_per_capita_by_countr').set_index("ISOcode")
data_sector = pd.read_excel(name, sheet_name='fossil_CO2_by_sector_and_countr').set_index("ISOcode")

#Name of years and sectors
years = list(range(1970, 2021))
sectors = list(set(data_sector.Sector))

#Preprocess data
data_total, data_capita, data_sector = preprocess(data_total, data_capita, data_sector)

vals = np.zeros((5, 52))
ind = 0
sector = sectors[0]
for index, row in data_sector.iterrows():
    if(row['Sector'] == sector):
      for i in range(0, 52):
        vals[ind][i] = vals[ind][i] + row[1970 + i]
    else:
      ind = ind + 1
      sector = row['Sector']



# App layout
app.layout = html.Div([
    dcc.Dropdown(
        options=[{'label': i, 'value': i} for i in list(data_total.index)],
        value='ABW',
        id='my-dmc-radio-item'
    ),
    html.Div([
        dcc.Graph(id='graph-placeholder')
    ]),
    dcc.Graph(id='pie-chart'),
    dcc.Slider(id='sector-slider',
              step=1,
              value=years[0],
              min=years[0],
              max=years[-1],
              marks = {i: str(i)[2:] for i in years},

    )

], className="container")


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)