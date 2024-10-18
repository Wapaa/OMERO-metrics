import dash
from dash import html
from django_plotly_dash import DjangoDash
import dash_mantine_components as dmc
import pandas as pd
from dash_iconify import DashIconify
from datetime import datetime

from pandas.io.formats.printing import justify

import OMERO_metrics.tools.dash_forms_tools as dft
import microscopemetrics_schema.datamodel as mm_schema

primary_color = "#008080"

stylesheets = [
    "https://unpkg.com/@mantine/dates@7/styles.css",
    "https://unpkg.com/@mantine/code-highlight@7/styles.css",
    "https://unpkg.com/@mantine/charts@7/styles.css",
    "https://unpkg.com/@mantine/carousel@7/styles.css",
    "https://unpkg.com/@mantine/notifications@7/styles.css",
    "https://unpkg.com/@mantine/nprogress@7/styles.css",
]
dashboard_name = "omero_project_dash"
dash_app_project = DjangoDash(
    name=dashboard_name,
    serve_locally=True,
    external_stylesheets=stylesheets,
)

dash_app_project.layout = dmc.MantineProvider(
    [
        dmc.Tabs(
            [
                dmc.TabsList(
                    [
                        dmc.TabsTab(
                            "Dashboard",
                            leftSection=DashIconify(
                                icon="fluent-mdl2:b-i-dashboard"
                            ),
                            value="dashboard",
                            color="#189A35",
                        ),
                        dmc.TabsTab(
                            "Settings",
                            leftSection=DashIconify(icon="tabler:settings"),
                            value="settings",
                            color="#189A35",
                        ),
                    ],
                    grow="True",
                    justify="space-around",
                    variant="light",
                ),
                dmc.TabsPanel(
                    dmc.Container(
                        [
                            dmc.Center(
                                [
                                    dmc.Group(
                                        [
                                            html.Img(
                                                src="./assets/images/logo.png",
                                                style={"width": "95px"},
                                            ),
                                            dmc.Title(
                                                "Project Dashboard",
                                                c="#189A35",
                                                size="h3",
                                                mb=10,
                                                mt=5,
                                            ),
                                        ]
                                    ),
                                ],
                                style={
                                    "background-color": "white",
                                    "border-radius": "0.5rem",
                                    "padding": "10px",
                                },
                            ),
                            dmc.Divider(
                                variant="solid",
                                style={"marginTop": 10, "marginBottom": 10},
                            ),
                            dmc.Grid(
                                [
                                    dmc.GridCol(
                                        [
                                            dmc.Select(
                                                id="project-dropdown",
                                                label="Select Measurement",
                                                w="auto",
                                                value="0",
                                                clearable=False,
                                                leftSection=DashIconify(
                                                    icon="radix-icons:magnifying-glass"
                                                ),
                                                rightSection=DashIconify(
                                                    icon="radix-icons:chevron-down"
                                                ),
                                            )
                                        ],
                                        span="3",
                                    ),
                                    dmc.GridCol(
                                        [
                                            dmc.DatePicker(
                                                id="date-picker",
                                                label="Select Date",
                                                valueFormat="DD-MM-YYYY",
                                                leftSection=DashIconify(
                                                    icon="clarity:date-line"
                                                ),
                                                type="range",
                                                w="auto",
                                            ),
                                        ],
                                        span="3",
                                    ),
                                ],
                                justify="space-between",
                                style={
                                    "padding": "10px",
                                    "borderTopLeftRadius": "0.5rem",
                                    "borderTopRightRadius": "0.5rem",
                                    "backgroundColor": "white",
                                    "margin-top": "10px",
                                },
                            ),
                            html.Div(
                                id="graph-project",
                                style={"background-color": "white"},
                            ),
                            dmc.Divider(
                                variant="solid",
                                style={"marginTop": 10, "marginBottom": 10},
                            ),
                            html.Div(id="blank-input"),
                            html.Div(id="blank-output"),
                            html.Div(id="text_km"),
                            html.Div(
                                id="clickdata",
                                style={
                                    "background-color": "white",
                                    "align": "center",
                                },
                            ),
                        ],
                        fluid=True,
                        style={
                            "background-color": "white",
                            "margin": "10px",
                            "border-radius": "0.5rem",
                            "padding": "10px",
                        },
                    ),
                    value="dashboard",
                ),
                dmc.TabsPanel(
                    dmc.Container(
                        children=[
                            dmc.Grid(
                                [
                                    dmc.GridCol(
                                        id="input_parameters_container",
                                        span="auto",
                                    ),
                                    dmc.GridCol(
                                        id="sample_container", span="auto"
                                    ),
                                ],
                                justify="flex-end",
                                mt=10,
                                mb=10,
                            ),
                            dmc.Group(
                                [
                                    dmc.Button(
                                        "Update",
                                        id="modal-submit-button",
                                    ),
                                    dmc.Button(
                                        "Reset",
                                        color="red",
                                        variant="outline",
                                        id="modal-close-button",
                                    ),
                                ],
                                justify="center",
                                align="center",
                            ),
                        ],
                        fluid=True,
                        style={
                            "background-color": "white",
                            "margin": "10px",
                            "border-radius": "0.5rem",
                            "padding": "10px",
                        },
                    ),
                    value="settings",
                ),
            ],
            value="dashboard",
        )
    ]
)


@dash_app_project.expanded_callback(
    dash.dependencies.Output("project-dropdown", "data"),
    dash.dependencies.Output("date-picker", "minDate"),
    dash.dependencies.Output("date-picker", "maxDate"),
    dash.dependencies.Output("date-picker", "value"),
    [dash.dependencies.Input("blank-input", "children")],
)
def update_dropdown(*args, **kwargs):
    kkm = kwargs["session_state"]["context"]["kkm"]
    kkm = [k.replace("_", " ").title() for k in kkm]
    dates = kwargs["session_state"]["context"]["dates"]
    options = [{"value": f"{i}", "label": f"{k}"} for i, k in enumerate(kkm)]
    min_date = min(dates)
    max_date = max(dates)
    data = options
    value_date = [min_date, max_date]
    return data, min_date, max_date, value_date


@dash_app_project.expanded_callback(
    dash.dependencies.Output("graph-project", "children"),
    [
        dash.dependencies.Input("project-dropdown", "value"),
        dash.dependencies.Input("date-picker", "value"),
    ],
)
def update_table(*args, **kwargs):
    df_list = kwargs["session_state"]["context"]["key_measurements_list"]
    kkm = kwargs["session_state"]["context"]["kkm"]
    measurement = int(args[0])
    dates_range = args[1]
    dates = kwargs["session_state"]["context"]["dates"]
    df_filtering = pd.DataFrame(dates, columns=["Date"])
    df_dates = df_filtering[
        (
            df_filtering["Date"]
            >= datetime.strptime(dates_range[0], "%Y-%m-%d").date()
        )
        & (
            df_filtering["Date"]
            <= datetime.strptime(dates_range[1], "%Y-%m-%d").date()
        )
    ].index.to_list()
    # kkm = [k.replace("_", " ").title() for k in kkm]
    df_list_filtered = [df_list[i] for i in df_dates]
    data = [
        {"Date": dates[i], "Name": f"Dataset {i}"}
        | df[[kkm[measurement]]]
        .copy()
        .mean()
        .reset_index(name="Mean")
        .rename(columns={"index": "Measurement"})
        .pivot_table(columns="Measurement")
        .to_dict("records")[0]
        for i, df in enumerate(df_list_filtered)
    ]
    line = dmc.LineChart(
        id="line-chart",
        h=300,
        dataKey="Date",
        data=data,
        withLegend=True,
        legendProps={"horizontalAlign": "top", "height": 50},
        series=[{"name": kkm[measurement], "color": "green.7"}],
        curveType="natural",
        style={"padding": 20},
        xAxisLabel="Processed Date",
        # yAxisLabel=str(kkm[measurement]).replace("_", " ").title(),
    )

    return line


@dash_app_project.expanded_callback(
    dash.dependencies.Output("text_km", "children"),
    dash.dependencies.Output("clickdata", "children"),
    [dash.dependencies.Input("line-chart", "clickData")],
    prevent_initial_call=True,
)
def update_project_view(*args, **kwargs):
    if args[0]:
        table = kwargs["session_state"]["context"]["key_measurements_list"]
        dates = kwargs["session_state"]["context"]["dates"]
        kkm = kwargs["session_state"]["context"]["kkm"]
        selected_dataset = int(args[0]["Name"].split(" ")[-1])
        df_selected = table[selected_dataset]
        table_kkm = df_selected[kkm].copy()
        table_kkm = table_kkm.round(3)
        table_kkm.columns = table_kkm.columns.str.replace("_", " ").str.title()
        date = dates[selected_dataset]
        grid = dmc.ScrollArea(
            [
                dmc.Table(
                    striped=True,
                    data={
                        "head": table_kkm.columns.tolist(),
                        "body": table_kkm.values.tolist(),
                        "caption": "Key Measurements for the selected dataset",
                    },
                    highlightOnHover=True,
                    style={
                        "background-color": "white",
                        "width": "98%",
                        "height": "auto",
                        "margin": "20px",
                        "border-radius": "0.5rem",
                        "align": "center",
                    },
                )
            ]
        )
        return (
            dmc.Center(
                [
                    DashIconify(icon="gis:measure-line", color="#189A35"),
                    dmc.Text(
                        [
                            "Key Measurements" " processed at " + str(date),
                        ],
                        c="#189A35",
                        mt=10,
                        ml=10,
                        mr=10,
                        fw="bold",
                    ),
                ]
            ),
            grid,
        )

    else:
        return dash.no_update


@dash_app_project.expanded_callback(
    dash.dependencies.Output("input_parameters_container", "children"),
    dash.dependencies.Output("sample_container", "children"),
    [dash.dependencies.Input("blank-input", "children")],
)
def update_modal(*args, **kwargs):
    setup = kwargs["session_state"]["context"]["setup"]
    print("setup", setup)
    sample = setup["sample"]
    mm_sample = getattr(mm_schema, sample["type"])
    mm_sample = mm_sample(**sample["fields"])
    sample_form = dft.DashForm(
        mm_sample, disabled=False, form_id="sample_form"
    )
    input_parameters = setup["input_parameters"]
    mm_input_parameters = getattr(mm_schema, input_parameters["type"])
    mm_input_parameters = mm_input_parameters(**input_parameters["fields"])
    input_parameters_form = dft.DashForm(
        mm_input_parameters, disabled=False, form_id="input_parameters_form"
    )

    return (
        [dmc.Text("Input Parameters:"), input_parameters_form.form],
        [dmc.Text("Sample:"), sample_form.form],
    )


@dash_app_project.expanded_callback(
    dash.dependencies.Output("modal-simple", "opened"),
    [
        dash.dependencies.Input("modal-demo-button", "n_clicks"),
        dash.dependencies.Input("modal-close-button", "n_clicks"),
        dash.dependencies.Input("modal-submit-button", "n_clicks"),
        dash.dependencies.State("modal-simple", "opened"),
    ],
    prevent_initial_call=True,
)
def modal_demo(*args, **kwargs):
    opened = args[3]
    return not opened
