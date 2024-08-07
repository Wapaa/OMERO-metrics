#!/usr/bin/env python
#
# Copyright (c) 2024 University of Dundee.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import yaml

"""Integration tests for index page."""
from omero.gateway import ImageWrapper
from omeroweb.testlib import IWebTest, get
import pytest
from django.urls import reverse
from omero.gateway import BlitzGateway
from django.shortcuts import resolve_url
from structure_generator import generate_users_groups


def get_connection(user, group_id=None):
    """Get a BlitzGateway connection for the given user's client."""
    connection = BlitzGateway(client_obj=user[0])
    # Refresh the session context
    connection.getEventContext()
    if group_id is not None:
        connection.SERVICE_OPTS.setOmeroGroup(group_id)
    return connection


class TestLoadIndexPage(IWebTest):
    """Tests loading the index page."""

    @pytest.fixture()
    def user1(self):
        """Return a new user in a read-annotate group."""
        group = self.new_group(perms="rwrw--")
        user = self.new_client_and_user(privileges=None)
        return user

    @pytest.fixture(scope="session")
    def server_structure(self):
        with open("test/integration/server_structure.yaml", "r") as f:
            server_structure = yaml.load(f, Loader=yaml.SafeLoader)
        return server_structure

    def test_load_index(self, user1):
        """Test loading the app home page."""
        conn = get_connection(user1)
        user_name = conn.getUser().getName()
        django_client = self.new_django_client(user_name, user_name)
        index_url = reverse("OMERO_metrics_index")
        # asserts we get a 200 response code etc
        rsp = get(django_client, index_url)
        html_str = rsp.content.decode()
        assert "Microscope" in html_str

    @pytest.mark.django_db
    def test_app_lookup(self, user1):
        "Test looking up an existing application"
        from OMERO_metrics.dash_apps.plotly_apps import app

        from django_plotly_dash.models import get_stateless_by_name

        app2 = get_stateless_by_name(app._uid)

        assert app2
        assert app._uid == app2._uid
