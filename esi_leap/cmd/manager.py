import sys

from oslo_service import service

from esi_leap.common import service as esi_leap_service
import esi_leap.conf
from esi_leap.manager import service as manager_service


CONF = esi_leap.conf.CONF


def main():
    esi_leap_service.prepare_service(sys.argv)
    service.launch(
        CONF,
        manager_service.ManagerService(),
        restart_method='mutate'
    ).wait()
