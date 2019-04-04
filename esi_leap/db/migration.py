from oslo_config import cfg
from stevedore import driver

_IMPL = None


def get_backend():
    global _IMPL
    if not _IMPL:
        cfg.CONF.import_opt('backend', 'oslo_db.options', group='database')
        _IMPL = driver.DriverManager("esi_leap.database.migration_backend",
                                     cfg.CONF.database.backend).driver
    return _IMPL


def version():
    return get_backend().version()


def create_schema():
    return get_backend().create_schema()
