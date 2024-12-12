import json
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# -----------------------------------------
# Step 1: Load and Transform Your Data
# -----------------------------------------
df = pd.read_csv("./figure_friday/2024/week_49/data/megawatt_demand_2024.csv")  # Replace with your actual filename

# Parse timestamps
# The primary time column could be "UTC Timestamp (Interval Ending)" or the local one.
# We'll choose UTC for consistency.
df['timestamp'] = pd.to_datetime(df['UTC Timestamp (Interval Ending)'])

# Columns of interest for load data:
load_columns = [
    "Connecticut Actual Load (MW)",
    "Maine Actual Load (MW)",
    "New Hampshire Actual Load (MW)",
    "Northeast Massachusetts Actual Load (MW)",
    "Rhode Island Actual Load (MW)",
    "Southeast Massachusetts Actual Load (MW)",
    "Vermont Actual Load (MW)",
    "Western/Central Massachusetts Actual Load (MW)"
]

# Melt the dataframe from wide to long format
# We will have a 'region' column and a 'load_mw' column
df_melted = df.melt(
    id_vars=['timestamp'],
    value_vars=load_columns,
    var_name='region',
    value_name='load_mw'
)

# Clean up region names by removing " Actual Load (MW)"
df_melted['region'] = df_melted['region'].str.replace(' Actual Load \(MW\)', '', regex=True)

# Now the region column should look like:
# "Connecticut", "Maine", "New Hampshire", "Northeast Massachusetts",
# "Rhode Island", "Southeast Massachusetts", "Vermont", "Western/Central Massachusetts"

# Confirm the unique regions
print(df_melted['region'].unique())

# -----------------------------------------
# Step 2: Load GeoJSON
# -----------------------------------------
with open("./figure_friday/2024/week_49/data/new_england_geojson.json") as f:
    geojson = json.load(f)

# -----------------------------------------
# Step 3: Create the Initial Figures
# -----------------------------------------
# For the initial map, let's pick the latest timestamp in the data
latest_time = df_melted['timestamp'].max()
df_latest = df_melted[df_melted['timestamp'] == latest_time]

fig_map = px.choropleth_mapbox(
    df_latest,
    geojson=geojson,
    locations='region',
    featureidkey='properties.NAME',
    color='load_mw',
    color_continuous_scale="Viridis",
    mapbox_style="carto-positron",
    zoom=5,
    center={"lat": 43.5, "lon": -71.5},  # Approximate center of New England
    opacity=0.7,
    hover_name='region'
)
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

fig_line = px.line(
    df_melted,
    x='timestamp', y='load_mw', color='region',
    title='Load Over Time',
    labels={'load_mw':'Load (MW)', 'timestamp':'Time'}
)
fig_line.update_layout(hovermode="x unified")

# -----------------------------------------
# Step 4: Build the Dash App
# -----------------------------------------
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("New England Electricity Usage"),
    html.Div([
        html.Div([
            dcc.Graph(id='map', figure=fig_map, style={"height": "60vh"})
        ], style={"width": "40%", "display": "inline-block", "vertical-align": "top"}),

        html.Div([
            dcc.Graph(id='timeseries', figure=fig_line, style={"height": "60vh"})
        ], style={"width": "58%", "display": "inline-block", "padding-left":"2%", "vertical-align": "top"}),
    ])
])

@app.callback(
    Output('timeseries', 'figure'),
    Input('map', 'clickData')
)
def update_line_chart(clickData):
    # If no region clicked, show all
    if clickData is None:
        fig = px.line(
            df_melted, x='timestamp', y='load_mw', color='region',
            title='Load Over Time', labels={'load_mw':'Load (MW)', 'timestamp':'Time'}
        )
        fig.update_layout(hovermode="x unified")
        return fig

    # Extract the clicked region
    clicked_region = clickData['points'][0]['location']

    # Filter df for that region
    dff = df_melted[df_melted['region'] == clicked_region]
    fig = px.line(
        dff, x='timestamp', y='load_mw', color='region',
        title=f'Load Over Time: {clicked_region}',
        labels={'load_mw':'Load (MW)', 'timestamp':'Time'}
    )
    fig.update_layout(hovermode="x unified")
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
