import importlib

import esi_leap.conf

CONF = esi_leap.conf.CONF


def get_idp():
    module_path, class_name = CONF.esi.idp_plugin_class.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()
