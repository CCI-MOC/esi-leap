from oslo_serialization import jsonutils
from esi_leap.api.controllers import version


def root(host_url):
    return {
        "name": "ESI Leap API",
        "description": "ESI Leap is an OpenStack service for leasing baremetal nodes, designed to run on top of multi-tenant Ironic.",
        "default_version": version.default_version(host_url),
        "versions": version.all_versions(host_url),
    }


class Health(object):
    def __init__(self, app, path):
        self.app = app
        self.path = path

    def __call__(self, environ, start_response):
        if environ["PATH_INFO"] == self.path:
            start_response("200 OK", [("Content-Type", "application/json")])
            return [
                jsonutils.dump_as_bytes(
                    root(environ["wsgi.url_scheme"] + "://" + environ["HTTP_HOST"])
                )
            ]
        return self.app(environ, start_response)
