import dash
from dash import dcc, html, dash_table
from django_plotly_dash import DjangoDash
import dash_mantine_components as dmc

external_scripts = [
    # add the tailwind cdn url hosting the files with the utility classes
    {"src": "https://cdn.tailwindcss.com"}
]
stylesheets = [
    "https://unpkg.com/@mantine/dates@7/styles.css",
    "https://unpkg.com/@mantine/code-highlight@7/styles.css",
    "https://unpkg.com/@mantine/charts@7/styles.css",
    "https://unpkg.com/@mantine/carousel@7/styles.css",
    "https://unpkg.com/@mantine/notifications@7/styles.css",
    "https://unpkg.com/@mantine/nprogress@7/styles.css",
    "./assets/omero_metrics.css",
]
primary_color = "#63aa47"

app = DjangoDash(
    "PSF_Beads",
    external_stylesheets=stylesheets,
    external_scripts=external_scripts,
)


app.layout = dmc.MantineProvider(
    [
        dmc.Container(
            [
                dmc.Center(
                    [
                        dmc.Text(
                            id="title",
                            c=primary_color,
                            style={"fontSize": 30},
                        ),
                        dmc.Group(
                            [
                                html.Img(
                                    src="./assets/images/logo.png",
                                    style={"width": "100px"},
                                ),
                                dmc.Text(
                                    "OMERO Metrics Dashboard",
                                    c=primary_color,
                                    style={"fontSize": 15},
                                ),
                            ]
                        ),
                    ]
                ),
                dmc.Divider(variant="solid"),
                dmc.Stack(
                    [
                        dmc.Center(
                            [
                                dmc.Title(
                                    "Key Measurements",
                                    c="#189A35",
                                    size="h3",
                                    mb=10,
                                ),
                                dmc.Table(
                                    id="key_values_psf",
                                    striped=True,
                                    highlightOnHover=True,
                                    className="table table-striped table-bordered",
                                ),
                            ]
                        ),
                    ]
                ),
                dmc.Divider(variant="solid"),
                html.Div(id="blank-input"),
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
    dash.dependencies.Output("key_values_psf", "data"),
    [
        dash.dependencies.Input("blank-input", "children"),
    ],
)
def func_psf_callback(*args, **kwargs):
    table_km = kwargs["session_state"]["context"]["bead_km_df"]
    kkm = [
        "channel_name",
        "considered_valid_count",
        "intensity_max_median",
        "intensity_max_std",
        "intensity_min_mean",
        "intensity_min_median",
        "intensity_min_std",
        "intensity_std_mean",
        "intensity_std_median",
        "intensity_std_std",
    ]
    table_kkm = table_km[kkm].copy()
    table_kkm = table_kkm.round(3)
    table_kkm.columns = table_kkm.columns.str.replace("_", " ").str.title()
    data = {
        "head": table_kkm.columns.tolist(),
        "body": table_kkm.values.tolist(),
        "caption": "Key Measurements for the selected dataset",
    }
    return data
