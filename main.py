import pandas as pd
import numpy as np
from collections import Counter
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import dash_table
import dash_mantine_components as dmc

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


#Read csv
name = "data/CO2.xlsx"
data_total = pd.read_excel(name, sheet_name='fossil_CO2_totals_by_country').set_index("ISOcode")
data_capita = pd.read_excel(name, sheet_name='fossil_CO2_per_capita_by_countr').set_index("ISOcode")
data_sector = pd.read_excel(name, sheet_name='fossil_CO2_by_sector_and_countr').set_index("ISOcode")

# Display names for the sheets
sheet_names = ['fossil_CO2_per_capita_by_countr', 'fossil_CO2_totals_by_country']
dfs = {sheet_name: pd.read_excel(name, sheet_name=sheet_name) for sheet_name in sheet_names}
initial_sheet_name = 'fossil_CO2_per_capita_by_countr'

# Display names for the sheets
sheet_display_names = {
    'fossil_CO2_per_capita_by_countr': 'Fossil CO2 per Capita',
    'fossil_CO2_totals_by_country': 'Fossil CO2 in Total',
}

#Name of years and sectors
years = list(range(1970, 2021))
sectors = ['Power Industry', 'Buildings', 'Transport', 'Other industrial combustion', 'Other sectors']
dict_country = dict(zip(data_total['Country'], data_total.index))

#Preprocess data
data_total, data_capita, data_sector = preprocess(data_total, data_capita, data_sector)
country_dropdown = [{'label': country, 'value': country} for country in data_total['Country'].unique()]

#Vals to Sector
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

#simple lukas 1
@app.callback(
    Output('graph-basic', 'figure'),
    [Input('my-dmc-radio-item', 'value')]
)
def update_graph_line(col_chosen):
    col_chosen_ = dict_country[col_chosen]
    meadians = [np.median(data_capita.transpose().loc[i]) for i in years]
    
    fig = go.Figure()

    #fig = px.line(data_capita.transpose().loc[years], x=years, y=col_chosen_)
    fig.add_trace(go.Scatter(
        x=years,
        y=data_capita.transpose().loc[years][col_chosen_],
        mode='lines',
        name='Cosumption per capita'))
 
    fig.add_trace(go.Scatter(
        x=years,
        y=meadians,
        mode='lines',
        name='Median Cosumption per capita',
        line=dict(color='black')))

    fig.update_layout(xaxis_title='Year', yaxis_title='Mt CO2', title=col_chosen_)
    fig.update_layout(title = f"Mt CO2 emissions per capita in {col_chosen}" )
    fig.update_yaxes(range=[0, 25])
    return fig

#Pie
@app.callback(
    Output('pie-chart', 'figure'),
    [Input('sector-slider', 'value')]
)
def update_pie_chart(year):
    fig = px.pie(names=sectors, values=vals[:,years.index(year)], hole=0.5
    , title=f"CO2 emission by sector for {year}") 
    return fig

#Atlas

fig = px.choropleth(pd.melt(dfs[initial_sheet_name], id_vars=['ISOcode', 'Country'], var_name='Year', value_name='Value'),
                    locations='ISOcode',
                    color='Value',
                    hover_name='Country',
                    animation_frame='Year',
                    title='World Atlas Over Years (Mt CO2)',
                    color_continuous_scale='Plasma',
                    color_continuous_midpoint=15
                    )
fig.update_coloraxes(colorscale='Plasma', cmin=0, cmax=30)  # Set fixed range for the legend

@app.callback(
    Output('world-atlas', 'figure'),
    [Input('dropdown-sheet-selector', 'value')]
)
def update_figure(selected_sheet):
    if selected_sheet=="fossil_CO2_per_capita_by_countr":
      midpoint=15
    else:
      midpoint=500
    updated_fig = px.choropleth(pd.melt(dfs[selected_sheet], id_vars=['ISOcode', 'Country'], var_name='Year', value_name='Value'),
                                locations='ISOcode',
                                color='Value',
                                hover_name='Country',
                                animation_frame='Year',
                                title='World Atlas Over Years (Mt CO2)',
                                color_continuous_scale='Plasma',
                                color_continuous_midpoint=midpoint
                                )

    # Set static color scale for the legend
    updated_fig.update_coloraxes(colorscale='Plasma', cmin=0, cmax=midpoint*2)

    return updated_fig

#Sector quantiles
dicci = {}
sectors = ['Power Industry', 'Buildings', 'Transport', 'Other industrial combustion', 'Other sectors']
for sec in sectors:
  dicci[sec] = pd.DataFrame(columns=(['ISOcode'] + list(range(1970,2022))))

for sec in sectors:
  dicci[sec] = data_sector[data_sector['Sector'] == sec]
  dicci[sec].drop(['Sector', 'Country'], axis=1)
@app.callback(
    Output('graph-quantile', 'figure'),
    [Input('radio', 'value')]
)
def update_graph(col_chosen):

    vals_m = np.zeros(len(years))
    q_a = np.zeros(len(years))
    q_b = np.zeros(len(years))

    for year in years:
      i = year-1970
      vals_m[i] = np.median(np.array(dicci[col_chosen][year].tolist()))
      q_a[i] = np.quantile(np.array(dicci[col_chosen][year].tolist()),0.25)
      q_b[i] = np.quantile(np.array(dicci[col_chosen][year].tolist()),0.75)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years,
        y=q_b,
        fill='tonexty',
        name='Quantile 75%',
        mode='none', fillcolor='grey', opacity=0.01))

    fig.add_trace(go.Scatter(
        x=years,
        y=q_a,
        fill='tonexty',
        name='Quantile 25%',
        mode='none', fillcolor='grey', opacity=0.01))

    fig.add_trace(go.Scatter(
        x=years,
        y=vals_m,
        mode='lines',
        name='Median',
        line=dict(color='black')))

    fig.update_layout(xaxis_title='Year', yaxis_title='Mt CO2', title=col_chosen)
    fig.update_yaxes(range=[0, 25])
    return fig


# Barplot

@app.callback(
    Output('co2-changes-bar-chart', 'figure'),
    [Input('my-dmc-radio-item', 'value')]
)
def update_graph(selected_country):
    # Filter data for selected country
    selected_data = dict(data_total[data_total['Country'] == selected_country])

    diffs = np.zeros(len(years))
    for idx, i in enumerate(years[1:]):

        diffs[idx +1] = (list(selected_data[i])[0] / list(selected_data[i -1])[0] )* 100 - 100 #Mean = 0
    
    # Create figure with grouped bar chart
    fig = px.bar(x=years,
             y=diffs,
             labels={'x': 'Year', "y": "Growth(%)" },
             title=f'CO2 emission growth with respected to the previous year in {selected_country}',
             color_discrete_sequence=['blue'],
             opacity=0.7)

    return fig




def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.H1("CO2 emission dashboard"),
        ],
    )
def build_graph_title(title):
    return html.P(className="graph-title", children=title)


app.layout = html.Div(
    children=[
    html.Div(
        children = [
            build_banner(),

            dmc.Group( children = [
                dmc.Select(
                        data=[{'label': i, 'value': i} for i in sectors],
                        value='Power Industry',
                        id='radio'),
                dmc.Slider(id='sector-slider',
                        step=1,
                        value=years[0],
                        min=years[0],
                        max=years[-1],
                        marks = [{"label": i, "value": i} for i in years if i % 20 == 0])
            ], position = "center", grow = True
            ),
        ]
    ),
        html.Div(
            children=[
                dmc.Group( children = [
                    dcc.Graph(id='graph-quantile'),
                    dcc.Graph(id='pie-chart')],
                    position = "center", grow = True  

                ),
            ],
        ),
        html.Div(
            dmc.Group( 
                children= [ 
                    dmc.Select(
                    id='my-dmc-radio-item',
                    data=country_dropdown,
                    value='Aruba',  # Default selected country
                    searchable=True
                    ), 
                    ], position = "left", grow = True),
        ),
        html.Div(
            # Selected well productions
            id="well-production-container",
            className="six columns",
            children=[
                        dmc.Group( 
                        children=[
                            dcc.Graph(id="graph-basic"),
                            dcc.Graph(id="co2-changes-bar-chart"),
                            ],
                        position = "center", grow = True
                    ),
            ]),
        html.Div(
        children=[
            dmc.Select(
                    id='dropdown-sheet-selector',
                    data=[{'label': sheet_display_names[sheet_name], 'value': sheet_name} for sheet_name in sheet_names],
                    value=initial_sheet_name,)
        ],
    ),
    html.Div(
        id="top-row",
        children=[
            html.Div(
                className="row",
                id="top-row-graphs",
                # Well map
                children = [dcc.Graph(id='world-atlas', figure=fig,style={"width": "100%",'height': '70vh'})])]),
 
    ]
)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)