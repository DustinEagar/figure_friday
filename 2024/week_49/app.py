import json
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# -----------------------------------------
# Load and Prepare Data
# -----------------------------------------
df = pd.read_csv("./figure_friday/2024/week_49/data/megawatt_demand_2024.csv")  # Replace with your actual filename
df['timestamp'] = pd.to_datetime(df['UTC Timestamp (Interval Ending)'])

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

df_melted = df.melt(
    id_vars=['timestamp'],
    value_vars=load_columns,
    var_name='region',
    value_name='load_mw'
)

# Clean region names
df_melted['region'] = df_melted['region'].str.replace(' Actual Load \(MW\)', '', regex=True)

# Compute daily aggregates
df_melted['date'] = df_melted['timestamp'].dt.date
daily_agg = df_melted.groupby(['region', 'date']).agg(
    daily_avg=('load_mw', 'mean'),
    daily_min=('load_mw', 'min'),
    daily_max=('load_mw', 'max')
).reset_index()

print(df_melted.head())
print(daily_agg.head())
# Load GeoJSON
with open('./figure_friday/2024/week_49/data/new_england_geojson.json') as f:
    geojson = json.load(f)

# Define a color map for the regions
region_colors = {
    "Connecticut": "#1f77b4",
    "Maine": "#ff7f0e",
    "New Hampshire": "#2ca02c",
    "Northeast Massachusetts": "#d62728",
    "Rhode Island": "#9467bd",
    "Southeast Massachusetts": "#8c564b",
    "Vermont": "#e377c2",
    "Western/Central Massachusetts": "#7f7f7f"
}
# Create initial figures
latest_time = df_melted['timestamp'].max()
df_latest = df_melted[df_melted['timestamp'] == latest_time]
df_avg = df_melted.groupby('region').mean().reset_index()
print(df_avg.head())

fig_map = px.choropleth_mapbox(
    df_avg,
    geojson=geojson,
    locations='region',
    featureidkey='properties.NAME',
    color='load_mw',
    color_continuous_scale="Viridis",
    mapbox_style="carto-positron",
    zoom=5,
    center={"lat": 43.5, "lon": -71.5},  # Approx center of New England
    opacity=0.7,
    hover_name='region'
)
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, template='plotly_dark')

# Initial line plot: all regions
fig_line_all = px.line(
    df_melted,
    x='timestamp',
    y='load_mw',
    color='region',
    title='Load Over Time',
    labels={'load_mw':'Load (MW)', 'timestamp':'Time'},
    template='plotly_dark',
    color_discrete_map=region_colors
)
fig_line_all.update_layout(hovermode="x unified")

# Initial daily aggregates plot (blank or show all)
# We'll start with no selection - show all regions aggregated (optional)
fig_daily = go.Figure(layout={"template":"plotly_dark"})
fig_daily.update_layout(title="Daily Aggregate Load", xaxis_title="Date", yaxis_title="Load (MW)")

# -----------------------------------------
# Dash App
# -----------------------------------------
app = dash.Dash(__name__)

app.layout = html.Div(
    style={"backgroundColor": "#333", "color": "#fff", "padding": "20px"},  # Dark background
    children=[
        html.H1("New England Electricity Usage", style={"textAlign": "center"}),
        html.Div([
            html.Div([
                    html.H4('Average Load by ISO-NE Region'),
                    html.P("Click to filter by region"),
                dcc.Graph(id='map', figure=fig_map, style={"height": "60vh"})
            ], style={"width": "40%", "display": "inline-block", "vertical-align": "top"}),
            
            html.Div([
                dcc.Graph(id='timeseries', figure=fig_line_all, style={"height": "60vh"}),
                dcc.Graph(id='daily_timeseries', figure=fig_daily, style={"height": "60vh", "marginTop":"20px"})
            ], style={"width": "58%", "display": "inline-block", "padding-left":"2%", "vertical-align": "top"})
        ])
    ]
)

@app.callback(
    [Output('timeseries', 'figure'),
     Output('daily_timeseries', 'figure')],
    Input('map', 'clickData')
)
def update_charts(clickData):
    # If no region clicked, show all
    if clickData is None:
        # All regions time series
        fig_line = px.line(
            df_melted,
            x='timestamp', y='load_mw', color='region',
            title='Load Over Time', labels={'load_mw':'Load (MW)', 'timestamp':'Time'},
            template='plotly_dark'
        )
        fig_line.update_layout(hovermode="x unified")
        
        # Daily aggregates for all regions (optional): could just show empty
        fig_daily = go.Figure(layout={"template":"plotly_dark"})
        fig_daily.update_layout(title="Daily Aggregate Load", xaxis_title="Date", yaxis_title="Load (MW)")
        return fig_line, fig_daily

    # Extract clicked region
    clicked_region = clickData['points'][0]['location']

    # Filter data for the selected region
    dff = df_melted[df_melted['region'] == clicked_region]
    dff_daily = daily_agg[daily_agg['region'] == clicked_region]
    
    # Main time series for the selected region
    fig_line = px.line(
        dff, x='timestamp', y='load_mw', color='region',
        title=f'Load Over Time: {clicked_region}',
        labels={'load_mw':'Load (MW)', 'timestamp':'Time'},
        template='plotly_dark',
        color_discrete_map=region_colors
    )
    fig_line.update_layout(hovermode="x unified")
    
    # Daily aggregates: avg line, fill between min and max
    fig_daily = go.Figure(layout={"template":"plotly_dark"})
    fig_daily.add_trace(go.Scatter(
        x=dff_daily['date'], y=dff_daily['daily_max'],
        fill=None, mode='lines', line_color='rgba(200,50,50,0.5)',
        name='Daily Max'
    ))
    fig_daily.add_trace(go.Scatter(
        x=dff_daily['date'], y=dff_daily['daily_min'],
        fill='tonexty', mode='lines', line_color='rgba(50,50,200,0.5)',
        name='Daily Min'
    ))
    fig_daily.add_trace(go.Scatter(
        x=dff_daily['date'], y=dff_daily['daily_avg'],
        mode='lines', line_color='white', name='Daily Avg'
    ))

    fig_daily.update_layout(
        title=f"Daily Aggregate Load: {clicked_region}",
        xaxis_title="Date",
        yaxis_title="Load (MW)",
        hovermode="x unified"
    )

    return fig_line, fig_daily

if __name__ == '__main__':
    app.run_server(debug=True)
