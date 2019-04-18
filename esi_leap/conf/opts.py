import esi_leap.conf

_opts = [
    ('ironic', esi_leap.conf.ironic.list_opts()),
]


def list_opts():
    return _opts
