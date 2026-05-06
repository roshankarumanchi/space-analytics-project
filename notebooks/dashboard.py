# ============================================
# INTERACTIVE DASHBOARD
# ============================================
# Purpose: Combine all visualisations into
# a single interactive Plotly Dash dashboard
# Required by the project rubric
# ============================================

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from sqlalchemy import create_engine

# ============================================
# STEP 1: LOAD DATA FROM POSTGRESQL
# ============================================
engine = create_engine("postgresql://postgres:admin123@localhost:5432/space_project")

df_flares = pd.read_sql("SELECT * FROM nasa_solar_flares", engine)
df_satellites = pd.read_sql("SELECT * FROM ucs_satellites", engine)
df_launches = pd.read_sql("SELECT * FROM gcat_launches", engine)

# ============================================
# STEP 2: PREPARE COMBINED YEARLY DATA
# ============================================
launches_per_year = df_launches.groupby('launch_year').size().reset_index()
launches_per_year.columns = ['year', 'total_launches']

satellites_per_year = df_satellites.groupby('launch_year').size().reset_index()
satellites_per_year.columns = ['year', 'satellites_deployed']

flares_per_year = df_flares.groupby('year').size().reset_index()
flares_per_year.columns = ['year', 'solar_flares']

df_combined = launches_per_year.merge(satellites_per_year, on='year', how='outer')
df_combined = df_combined.merge(flares_per_year, on='year', how='outer')
df_combined = df_combined.fillna(0)
df_combined = df_combined.sort_values('year')
df_combined = df_combined[df_combined['year'] >= 1957]

# ============================================
# STEP 3: CREATE THE DASH APP
# ============================================
app = dash.Dash(__name__)

app.layout = html.Div(style={'fontFamily': 'Arial', 'padding': '20px', 'backgroundColor': '#f8f9fa'}, children=[

    # Title
    html.H1("Global Space Activity Dashboard",
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '5px'}),

    html.P("A Comprehensive Analysis of Rocket Launches, Satellite Deployment and Solar Activity (1957-2026)",
           style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'}),

    # --- Row 1: Summary Cards ---
    html.Div(style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'}, children=[
        html.Div(style={'backgroundColor': '#3498db', 'color': 'white', 'padding': '20px',
                        'borderRadius': '10px', 'textAlign': 'center', 'width': '22%'}, children=[
            html.H3(f"{len(df_launches):,}"),
            html.P("Total Launches")
        ]),
        html.Div(style={'backgroundColor': '#2ecc71', 'color': 'white', 'padding': '20px',
                        'borderRadius': '10px', 'textAlign': 'center', 'width': '22%'}, children=[
            html.H3(f"{len(df_satellites):,}"),
            html.P("Active Satellites")
        ]),
        html.Div(style={'backgroundColor': '#e74c3c', 'color': 'white', 'padding': '20px',
                        'borderRadius': '10px', 'textAlign': 'center', 'width': '22%'}, children=[
            html.H3(f"{len(df_flares):,}"),
            html.P("Solar Flares Recorded")
        ]),
        html.Div(style={'backgroundColor': '#9b59b6', 'color': 'white', 'padding': '20px',
                        'borderRadius': '10px', 'textAlign': 'center', 'width': '22%'}, children=[
            html.H3(f"{int(df_combined['year'].max()) - int(df_combined['year'].min())}"),
            html.P("Years of Data")
        ]),
    ]),

    # --- Row 2: Year Range Slider ---
    html.Div(style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': 'white',
                    'borderRadius': '10px'}, children=[
        html.Label("Select Year Range:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
        dcc.RangeSlider(
            id='year-slider',
            min=1957,
            max=2026,
            step=1,
            value=[1990, 2026],
            marks={i: str(i) for i in range(1960, 2030, 10)},
        )
    ]),

    # --- Row 3: Launches Over Time + Satellites by Orbit ---
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'}, children=[
        html.Div(style={'width': '48%', 'backgroundColor': 'white', 'borderRadius': '10px', 'padding': '10px'}, children=[
            dcc.Graph(id='launches-chart')
        ]),
        html.Div(style={'width': '48%', 'backgroundColor': 'white', 'borderRadius': '10px', 'padding': '10px'}, children=[
            dcc.Graph(id='orbit-pie')
        ]),
    ]),

    # --- Row 4: Flare Classes + Top Countries ---
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'}, children=[
        html.Div(style={'width': '48%', 'backgroundColor': 'white', 'borderRadius': '10px', 'padding': '10px'}, children=[
            dcc.Graph(id='flare-bar')
        ]),
        html.Div(style={'width': '48%', 'backgroundColor': 'white', 'borderRadius': '10px', 'padding': '10px'}, children=[
            dcc.Graph(id='country-bar')
        ]),
    ]),

    # --- Row 5: Satellite Purpose Dropdown + Chart ---
    html.Div(style={'backgroundColor': 'white', 'borderRadius': '10px', 'padding': '20px', 'marginBottom': '20px'}, children=[
        html.Label("Select Satellite Purpose:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='purpose-dropdown',
            options=[{'label': p, 'value': p} for p in df_satellites['Purpose'].value_counts().head(8).index],
            value='Communications',
            style={'marginBottom': '15px'}
        ),
        dcc.Graph(id='purpose-chart')
    ]),
])

# ============================================
# STEP 4: CALLBACKS (INTERACTIVITY)
# ============================================

# Callback 1: Update launches chart based on year slider
@app.callback(
    Output('launches-chart', 'figure'),
    Input('year-slider', 'value')
)
def update_launches(year_range):
    filtered = df_combined[(df_combined['year'] >= year_range[0]) & (df_combined['year'] <= year_range[1])]
    fig = px.line(filtered, x='year', y='total_launches',
                  title='Space Launches Per Year',
                  labels={'year': 'Year', 'total_launches': 'Number of Launches'})
    fig.update_traces(line=dict(color='royalblue', width=2))
    fig.update_layout(template='plotly_white')
    return fig

# Callback 2: Update orbit pie chart
@app.callback(
    Output('orbit-pie', 'figure'),
    Input('year-slider', 'value')
)
def update_orbit_pie(year_range):
    filtered = df_satellites[(df_satellites['launch_year'] >= year_range[0]) & (df_satellites['launch_year'] <= year_range[1])]
    orbit_counts = filtered['Class of Orbit'].value_counts().reset_index()
    orbit_counts.columns = ['Orbit_Class', 'Count']
    fig = px.pie(orbit_counts, values='Count', names='Orbit_Class',
                 title='Satellites by Orbit Class',
                 color_discrete_sequence=px.colors.qualitative.Set2)
    return fig

# Callback 3: Update flare bar chart
@app.callback(
    Output('flare-bar', 'figure'),
    Input('year-slider', 'value')
)
def update_flare_bar(year_range):
    filtered = df_flares[(df_flares['year'] >= year_range[0]) & (df_flares['year'] <= year_range[1])]
    flare_counts = filtered['flare_class'].value_counts().reset_index()
    flare_counts.columns = ['Flare_Class', 'Count']
    fig = px.bar(flare_counts, x='Flare_Class', y='Count',
                 title='Solar Flare Distribution',
                 color='Flare_Class',
                 color_discrete_sequence=['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#8e44ad'])
    fig.update_layout(template='plotly_white')
    return fig

# Callback 4: Update top countries chart
@app.callback(
    Output('country-bar', 'figure'),
    Input('year-slider', 'value')
)
def update_countries(year_range):
    filtered = df_satellites[(df_satellites['launch_year'] >= year_range[0]) & (df_satellites['launch_year'] <= year_range[1])]
    country_counts = filtered['Country of Operator/Owner'].value_counts().head(10).reset_index()
    country_counts.columns = ['Country', 'Count']
    country_counts = country_counts.sort_values('Count', ascending=True)
    fig = px.bar(country_counts, x='Count', y='Country', orientation='h',
                 title='Top 10 Countries by Satellites',
                 color='Count', color_continuous_scale='Blues')
    fig.update_layout(template='plotly_white')
    return fig

# Callback 5: Update purpose chart based on dropdown
@app.callback(
    Output('purpose-chart', 'figure'),
    Input('purpose-dropdown', 'value')
)
def update_purpose(selected_purpose):
    filtered = df_satellites[df_satellites['Purpose'] == selected_purpose]
    yearly = filtered.groupby('launch_year').size().reset_index()
    yearly.columns = ['Year', 'Count']
    fig = px.area(yearly, x='Year', y='Count',
                  title=f'{selected_purpose} Satellites Launched Per Year',
                  labels={'Count': 'Number of Satellites'})
    fig.update_layout(template='plotly_white')
    return fig

# ============================================
# STEP 5: RUN THE DASHBOARD
# ============================================
if __name__ == '__main__':
    app.run(debug=True)