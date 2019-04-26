import socket

from oslo_config import cfg


opts = [
    cfg.StrOpt("host",
               default=socket.gethostname()),
]


def register_opts(conf):
    conf.register_opts(opts)


def list_opts():
    return {'DEFAULT': opts}
