OMERO.metrics with Docker
=======================

A webapp to follow microscope performance over time.

Installation
============

Install `omero_metrics` in development mode as follows:

    # within your python venv:
    $ cd OMERO-metrics
    $ pip install -e .

Run in your terminal to start the server:

    $ docker compose up -d


Execute the following commands to create the database:

    $ docker exec -it omero-web /bin/bash /opt/omero/web/venv3/bin/python /opt/omero/web/venv3/lib/python3.10/site-packages/omeroweb/manage.py migrate

Execute this code to generate some test data:

     $ cd OMERO-metrics/
     $ pip install -r requirements.txt
     $ cd test/omero-server
     $ python3 structure_generator.py

Now restart your `omero-web` server and go to
<http://localhost:5080/omero_metrics/> in your browser.





# OMERO-metrics with a local omero-web

This project is related to configuring Django settings for OMERO web application with Plotly Dash components.

## Installation

```
$ cd OMERO-metrics
$ pip install -e .
```

1. Add the following lines to the `omeroweb/settings.py` file:
2. Make sure you have REACT_VERSION=18.2.0 installed.

```python
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django_plotly_dash.finders.DashAssetFinder',
    'django_plotly_dash.finders.DashComponentFinder',
    'django_plotly_dash.finders.DashAppDirectoryFinder',
]

PLOTLY_COMPONENTS = ['dpd_components', 'dash_bootstrap_components', 'dash_iconify', 'dash_mantine_components', 'dpd_static_support']

X_FRAME_OPTIONS = 'SAMEORIGIN'

PLOTLY_DASH = {
   'ws_route' :   'dpd/ws/channel',
    'http_route' : 'dpd/views',
   'http_poke_enabled' : True,
  'insert_demo_migrations' : False,
    'cache_timeout_initial_arguments': 60,
   'view_decorator': None,
  'cache_arguments': False,
   'serve_locally': False,
}
```


you need to manually add the following apps to the `INSTALLED_APPS` list in the `omeroweb/settings.py` file:

```python
"dpd_static_support",  "bootstrap4",  "corsheaders"
```


Add these additional configurations using the terminal:

    export OMERODIR=$(pwd)
    omero config set omero.web.application_server development
    omero config set omero.web.debug True
    omero config append omero.web.server_list '["localhost", 6063, "host"]'
    omero config append omero.web.apps '"omero_metrics"'
    omero config append omero.web.apps '"django_plotly_dash"'
    omero config append omero.web.ui.top_links '["Metrics", "metrics_index", {"title": "Open app in new tab", "target": "_blank"}]'
    omero config append omero.web.middleware '{"index": 0.5, "class": "corsheaders.middleware.CorsMiddleware"}'
    omero config append omero.web.middleware '{"index": 10, "class": "corsheaders.middleware.CorsPostCsrfMiddleware"}'
    omero config set omero.web.cors_origin_allow_all True
    omero config set omero.web.databases '{"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "mydatabase"}}'
    omero config append omero.web.middleware '{"index": 7, "class": "django_plotly_dash.middleware.ExternalRedirectionMiddleware"}'
    omero config append omero.web.middleware '{"index": 0.5, "class": "whitenoise.middleware.WhiteNoiseMiddleware"}'
    omero config append omero.web.middleware '{"index": 8, "class": "django_plotly_dash.middleware.BaseMiddleware"}'
    omero config append omero.web.middleware '{"index":0.1, "class": "omero_metrics.middleware.OmeroAuth"}'
    omero config append omero.web.ui.center_plugins '["Metrics View", "metrics/webclient_plugins/center_plugin.metricsview.js.html", "metrics_view_panel"]'
    omero config append omero.web.ui.right_plugins '["ROIs", "metrics/webclient_plugins/right_plugin.rois.js.html", "image_roi_tab"]'


```
python manage.py migrate
```


Further Info
============

1.  This app was derived from [cookiecutter-omero-webapp](https://github.com/ome/cookiecutter-omero-webapp).
2.  For further info on depolyment, see [Deployment](https://docs.openmicroscopy.org/latest/omero/developers/Web/Deployment.html)


