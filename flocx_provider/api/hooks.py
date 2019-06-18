
from pecan import hooks

from flocx_provider.db import api as db_api


class DBHook(hooks.PecanHook):
    """Create a db connection instance."""

    def before(self, state):
        state.request.db_conn = db_api.Connection()
