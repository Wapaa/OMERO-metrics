import dash
from dash import dcc, html
from django_plotly_dash import DjangoDash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

content = dmc.Card(
    children=[
        dmc.Group(
            [
                dmc.Text("Norway Fjord Adventures", fw=500),
                dmc.Badge("On Sale", color="pink"),
            ],
            justify="space-between",
            mt="md",
            mb="xs",
        ),
        dmc.Text(
            "With Fjord Tours you can explore more of the magical fjord landscapes with tours and activities on and "
            "around the fjords of Norway",
            size="sm",
            c="dimmed",
        ),
    ],
    withBorder=True,
    shadow="sm",
    radius="md",
    w=350,
)

dashboard_name = "Microscope"
dash_app_microscope = DjangoDash(
    name=dashboard_name,
    serve_locally=True,
)

dash_app_microscope.layout = dmc.MantineProvider(
    [
        dmc.Container(
            [
                dmc.Grid(
                    [
                        dmc.GridCol(
                            [
                                content,
                            ],
                            span="auto",
                        ),
                        dmc.GridCol(
                            [
                                content,
                            ],
                            span="auto",
                        ),
                        dmc.GridCol(
                            [
                                content,
                            ],
                            span="auto",
                        ),
                    ],
                    style={
                        "margin-top": "20px",
                        "background-color": "transparent",
                    },
                    justify="center",
                    align="center",
                    gutter="xl",
                ),
                dmc.Grid(
                    [],
                    style={
                        "margin-top": "20px",
                        "background-color": "transparent",
                    },
                    justify="center",
                ),
            ],
            style={"background-color": "#e0e0e0"},
            fluid=True,
        ),
    ]
)
