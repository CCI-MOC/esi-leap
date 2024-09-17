#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from esi_leap.common import health
from esi_leap.api.controllers import version
from esi_leap.tests import base
from oslo_serialization import jsonutils


class TestRootFunction(base.TestCase):
    def test_root(self):
        host_url = "http://example.com"
        expected_result = {
            "name": "ESI Leap API",
            "description": "ESI Leap is an OpenStack service for leasing baremetal nodes, designed to run on top of multi-tenant Ironic.",
            "default_version": version.default_version(host_url),
            "versions": version.all_versions(host_url),
        }
        result = health.root(host_url)
        self.assertEqual(result, expected_result)


class TestHealthMiddleware(base.TestCase):
    def setUp(self):
        super().setUp()
        self.app = self.simple_app
        self.path = "/health"
        self.health = health.Health(self.app, self.path)

    def simple_app(self, environ, start_response):
        start_response("401 Unauthorized", [("Content-Type", "text/plain")])
        return [b"401 Unauthorized"]

    def start_response(self, status, headers):
        self.status = status
        self.headers = headers

    def test_health_path(self):
        environ = {
            "PATH_INFO": self.path,
            "wsgi.url_scheme": "http",
            "HTTP_HOST": "example.com",
        }
        result = self.health(environ, self.start_response)
        self.assertEqual(self.status, "200 OK")
        self.assertEqual(dict(self.headers)["Content-Type"], "application/json")
        expected_body = jsonutils.dump_as_bytes(health.root("http://example.com"))
        self.assertEqual(result, [expected_body])

    def test_non_health_path(self):
        environ = {
            "PATH_INFO": "/not_health",
            "wsgi.url_scheme": "http",
            "HTTP_HOST": "example.com",
        }
        result = self.health(environ, self.start_response)
        self.assertEqual(self.status, "401 Unauthorized")
        self.assertEqual(dict(self.headers)["Content-Type"], "text/plain")
        self.assertEqual(result, [b"401 Unauthorized"])
