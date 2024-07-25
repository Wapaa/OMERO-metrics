import dash
from dash import dcc, html
from django_plotly_dash import DjangoDash
import dash_mantine_components as dmc
from ..tools.data_preperation import crop_bead_index, image_3d_chart
import plotly.express as px
from .utilities.dash_utilities import image_heatmap_setup
import numpy as np
import logging
import json

logger = logging.getLogger(__name__)


app = DjangoDash("PSF_Beads_image")

app.layout = dmc.MantineProvider(
    children=[
        dmc.Container(
            [
                html.Div(id="blank-input", children=[]),
                dmc.Stack(
                    [
                        dmc.Center(
                            dmc.Text(
                                "PSF Beads Dashboard for Image",
                                mb=30,
                                style={"margin-top": "20px", "fontSize": 40},
                            ),
                        ),
                        dcc.Dropdown(
                            value="channel 0",
                            id="channel_ddm_psf",
                            clearable=False,
                        ),
                        dcc.Graph(
                            id="image",
                            figure={},
                            style={
                                "display": "inline-block",
                                "width": "100%",
                                "height": "100%;",
                            },
                        ),
                        dcc.Graph(id="projection_graph", figure={}),
                        html.Div(id="test15"),
                        html.Div(id="test16"),
                    ]
                ),
            ],
            fluid=True,
            style={
                "background-color": "#eceff1",
                "margin": "20px",
                "border-radius": "0.5rem",
                "padding": "10px",
            },
        )
    ]
)


@app.expanded_callback(
    dash.dependencies.Output("image", "figure"),
    dash.dependencies.Output("channel_ddm_psf", "options"),
    [
        dash.dependencies.Input("channel_ddm_psf", "value"),
    ],
)
def update_image(*args, **kwargs):
    image_omero = kwargs["session_state"]["context"]["image"]
    channel_index = int(args[0].split(" ")[-1])
    min_distance = kwargs["session_state"]["context"]["min_distance"]
    channel_names = kwargs["session_state"]["context"]["channel_names"]
    channel_options = [
        {"label": c.name, "value": f"channel {i}"}
        for i, c in enumerate(channel_names.channels)
    ]
    bead_properties_df = kwargs["session_state"]["context"][
        "bead_properties_df"
    ]
    df_beads_location = bead_properties_df[
        bead_properties_df["channel_nr"] == channel_index
    ][
        [
            "channel_nr",
            "bead_id",
            "considered_axial_edge",
            "center_z",
            "center_y",
            "center_x",
        ]
    ].copy()
    ima = image_omero[0, :, :, :, :]
    list_chan = [c.name for c in channel_names.channels]
    stack = image_omero[0, :, :, :, channel_index]
    stack_z = np.max(stack, axis=0)
    fig, f = image_heatmap_setup(
        list_chan, ima, df_beads_location, min_distance=min_distance
    )
    return fig, channel_options


@app.expanded_callback(
    dash.dependencies.Output("test15", "children"),
    dash.dependencies.Output("test16", "children"),
    [
        dash.dependencies.Input("image", "clickData"),
        dash.dependencies.Input("image", "restyleData"),
    ],
    prevent_initial_call=True,
)
def updatemip(*args, **kwargs):
    point = args[0]["points"][0]
    logger.warning(
        f"Project {args[0]} is going to be linked to a different OMERO project."
    )
    return json.dumps(args[0], indent=2), json.dumps(args[1], indent=2)
