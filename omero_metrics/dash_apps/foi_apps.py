import uuid
import random
from datetime import datetime
import pandas as pd
from django.core.cache import cache
from django.utils.translation import gettext, gettext_lazy
import dash
from dash import Dash, dcc, html, Input, Output, callback,dash_table
from dash.dependencies import MATCH, ALL
import plotly.graph_objs as go
import dpd_components as dpd
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
from django_plotly_dash.consumers import send_to_pipe_channel
import plotly.express as px
import dash_mantine_components as dmc


c1 = "#d8f3dc"
c2 = "#eceff1"
c3 = "#5f7f53"



app = DjangoDash('FOI_Demo')

app.layout = dmc.Container([
      dmc.Center(
            dmc.Text(
                "Field Of Illumination Dashboard",
                color="#5f7f53",
                mb=30,
                style={"margin-top": "20px", "fontSize": 40},
            )
        ),
     
               dmc.Grid(
            [
               
                dmc.Col(
                    [
                        dmc.Stack(
                            [
                                dmc.Grid(
                                    [
                                        dmc.Col(
                                            [
                                                html.H3("Select Category"),
                                                dcc.Dropdown(
                                                    ['ch1', 'ch2', 'ch3'], value="ch3", id="key_dpd"
                                                ),
                                            ],
                                            span="auto",
                                            style={"background-color": c2, "margin-right": "10px"},
                                        ),
                                        dmc.Col(
                                            [
                                                html.H3("Select Date"),
                                                dcc.DatePickerRange(
                                                    id="date_filter",
                                                    start_date_placeholder_text="Start Period",
                                                    end_date_placeholder_text="End Period",
                                                ),
                                            ],
                                            span="auto",
                                        ),
                                    ],
                                ),
                                dmc.Title(
                                    "Key Measurments for FOI", color="#5f7f53", size="h3", mb=10
                                ),
                                dash_table.DataTable(
                                    id="table",
                                    page_size=10,
                                    sort_action="native",
                                    sort_mode="multi",
                                    sort_as_null=["", "No"],
                                    sort_by=[{"column_id": "pop", "direction": "asc"}],
                                    editable=False,
                                    style_cell={
                                        "textAlign": "left",
                                        "fontSize": 10,
                                        "font-family": "sans-serif",
                                    },
                                    style_header={
                                        "backgroundColor": "#5f7f53",
                                        "fontWeight": "bold",
                                        "fontSize": 15,
                                    },
                                ),
                            ]
                        )
                    ],
                    span="auto",
                    style={
                        "background-color": c2,
                        "margin-right": "10px",
                        "border-radius": "0.5rem",
                    },
                ),
                dmc.Col(
                    [
                        dmc.Title("Plot Over Time", color="#189A35", size="h3", mb=10),
                        dcc.Graph(id="graph_line", figure={}),
                    ],
                    span="auto",
                    style={"background-color": "#eceff1", "border-radius": "5px"},
                ),
            ],
            justify="space-between",
            align="stretch",
            gutter="xl",
            style={
                "margin-top": "20px",
            },
        ),
      
      
])

@app.expanded_callback(
    dash.dependencies.Output('table', 'data'),
    [dash.dependencies.Input('key_dpd', 'value'),])
def keyvalue_callback(*args, **kwargs):
    data = kwargs['session_state']['data']
    return data.to_dict('records')