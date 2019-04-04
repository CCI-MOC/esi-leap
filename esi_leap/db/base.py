import esi_leap.db.api


class Base(object):
    """DB driver is injected in the init method."""

    def __init__(self):
        super(Base, self).__init__()
        self.db = esi_leap.db.api
