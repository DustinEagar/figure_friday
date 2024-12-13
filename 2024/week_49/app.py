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

# Get unique dates for slider (daily granularity)
unique_dates = sorted(daily_agg['date'].unique())

# Identify month start dates
month_starts = [(i, d) for i, d in enumerate(unique_dates) if d.day == 1]

# Create marks only for the first of each month
date_marks = {i: d.strftime("%Y-%m-%d") for i, d in month_starts}

# Initial state: use the full range of dates
start_idx = 0
end_idx = len(unique_dates) - 1
start_date = unique_dates[start_idx]
end_date = unique_dates[end_idx]

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
        ]),
                    html.Div([
                dcc.RangeSlider(
                    id='date-range-slider',
                    min=0,
                    max=len(unique_dates)-1,
                    value=[start_idx, end_idx],
                    marks=date_marks,
                    step=1,
                    tooltip=None
                ),
            ], style={"margin-bottom":"20px"})
    ]
)

@app.callback(
    [Output('map', 'figure'),
     Output('timeseries', 'figure'),
     Output('daily_timeseries', 'figure')],
    [Input('map', 'clickData'),
     Input('date-range-slider', 'value')]
)
def update_charts(clickData, slider_value):
    start_idx, end_idx = slider_value
    start_date = unique_dates[start_idx]
    end_date = unique_dates[end_idx]

    df_map_day = df_melted[(df_melted['date'] >= start_date) & (df_melted['date'] <= end_date)].groupby(
        'region'
    ).mean().reset_index()
    df_line = df_melted[(df_melted['date'] >= start_date) & (df_melted['date'] <= end_date)]
    df_line_daily = daily_agg[(daily_agg['date'] >= start_date) & (daily_agg['date'] <= end_date)]

    if clickData is None:
        # No region clicked: show all regions
        fig_map = px.choropleth_mapbox(
            df_map_day,
            geojson=geojson,
            locations='region',
            featureidkey='properties.NAME',
            color='load_mw',
            color_continuous_scale="Viridis",
            mapbox_style="carto-positron",
            zoom=5,
            center={"lat": 43.5, "lon": -71.5},
            opacity=0.7,
            hover_name='region'
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, template='plotly_dark')

        fig_line = px.line(
            df_line, x='timestamp', y='load_mw', color='region',
            title='Load Over Time (Selected Date Range)',
            labels={'load_mw':'Load (MW)', 'timestamp':'Time'},
            template='plotly_dark',
            color_discrete_map=region_colors
        )
        fig_line.update_layout(hovermode="x unified")

        fig_daily = go.Figure(layout={"template":"plotly_dark"})
        fig_daily.update_layout(title="Daily Aggregate Load", xaxis_title="Date", yaxis_title="Load (MW)")

        return fig_map, fig_line, fig_daily

    # Region clicked
    clicked_region = clickData['points'][0]['location']
    dff = df_line[df_line['region'] == clicked_region]
    dff_daily = df_line_daily[df_line_daily['region'] == clicked_region]

    fig_map = px.choropleth_mapbox(
        df_map_day,
        geojson=geojson,
        locations='region',
        featureidkey='properties.NAME',
        color='load_mw',
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=5,
        center={"lat": 43.5, "lon": -71.5},
        opacity=0.7,
        hover_name='region'
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, template='plotly_dark')

    fig_line = px.line(
        dff, x='timestamp', y='load_mw', color='region',
        title=f'Load Over Time: {clicked_region} ({start_date} to {end_date})',
        labels={'load_mw':'Load (MW)', 'timestamp':'Time'},
        template='plotly_dark',
        color_discrete_map=region_colors
    )
    fig_line.update_layout(hovermode="x unified")

    fig_daily = go.Figure(layout={"template":"plotly_dark"})
    region_color = region_colors.get(clicked_region, "white")

    if not dff_daily.empty:
        fig_daily.add_trace(go.Scatter(
            x=dff_daily['date'], y=dff_daily['daily_max'],
            mode='lines', line_color=region_color,
            name='Daily Max'
        ))
        fig_daily.add_trace(go.Scatter(
            x=dff_daily['date'], y=dff_daily['daily_min'],
            fill='tonexty', mode='lines', line_color=region_color,
            name='Daily Min'
        ))
        fig_daily.add_trace(go.Scatter(
            x=dff_daily['date'], y=dff_daily['daily_avg'],
            mode='lines+markers', line_color='white', name='Daily Avg'
        ))

    fig_daily.update_layout(
        title=f"Daily Aggregate Load: {clicked_region}",
        xaxis_title="Date",
        yaxis_title="Load (MW)",
        hovermode="x unified"
    )

    return fig_map, fig_line, fig_daily

if __name__ == '__main__':
    app.run_server(debug=True)