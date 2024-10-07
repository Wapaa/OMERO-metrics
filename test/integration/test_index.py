from omero.gateway import ProjectWrapper
from omeroweb.testlib import IWebTest, get
import pytest
from django.urls import reverse
from omero.gateway import BlitzGateway


def get_connection(user, group_id=None):
    """Get a BlitzGateway connection for the given user's client."""
    connection = BlitzGateway(client_obj=user[0])
    connection.getEventContext()
    if group_id is not None:
        connection.SERVICE_OPTS.setOmeroGroup(group_id)
    return connection


class TestLoadIndexPage(IWebTest):
    """Tests loading the index page."""

    @pytest.fixture()
    def user1(self):
        """Return a new user in a read-annotate group."""
        # group = self.new_group(perms="rwrw--")
        user = self.new_client_and_user(privileges=None)
        return user

    # @pytest.fixture(scope="session")
    # def server_structure(self):
    #     with open("test/integration/server_structure.yaml", "r") as f:
    #         server_structure = yaml.load(f, Loader=yaml.SafeLoader)
    #     return server_structure

    def test_load_index(self, user1):
        """Test loading the app index page"""
        conn = get_connection(user1)
        user_name = conn.getUser().getName()
        django_client = self.new_django_client(user_name, user_name)
        index_url = reverse("OMERO_metrics_index")
        rsp = get(django_client, index_url)
        html_str = rsp.content.decode()
        assert "Microscope" in html_str

    # @pytest.mark.django_db
    # def test_app_lookup(self, user1):
    #     """Test looking up an existing application"""
    #     from OMERO_metrics.dash_apps.plotly_apps import app
    #     from django_plotly_dash.models import get_stateless_by_name
    #
    #     app2 = get_stateless_by_name(app._uid)
    #     assert app2
    #     assert app._uid == app2._uid

    @pytest.mark.django_db
    def test_app_lookup_dataset_metrics(self, user1):
        """Test looking up an existing application for dataset foi"""
        from OMERO_metrics.dash_apps.dash_dataset_foi import (
            dash_app_dataset,
        )
        from django_plotly_dash.models import get_stateless_by_name

        app2 = get_stateless_by_name(dash_app_dataset._uid)
        assert app2
        assert dash_app_dataset._uid == app2._uid

    @pytest.mark.django_db
    def test_app_lookup_dataset_psf(self, user1):
        """Test looking up an existing application for dataset psf"""
        from OMERO_metrics.dash_apps.dash_dataset_psf_beads import (
            app,
        )
        from django_plotly_dash.models import get_stateless_by_name

        app2 = get_stateless_by_name(app._uid)
        assert app2
        assert app._uid == app2._uid

    @pytest.mark.django_db
    def test_load_project(self, user1):
        """Test loading the project dash view page."""
        conn = get_connection(user1)
        project = self.make_project(
            name="test_project", description="Project", client=conn.c
        )
        new_project = ProjectWrapper(conn, project)
        project_id = int(new_project.getId())
        user_name = conn.getUser().getName()
        django_client = self.new_django_client(user_name, user_name)
        index_url = reverse("project", args=[project_id])
        response = get(django_client, index_url)
        html_str = response.content.decode()
        assert "Omero Metrics" in html_str
