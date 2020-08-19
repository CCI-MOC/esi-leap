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

import datetime
import mock
from oslo_context import context as ctx
from oslo_utils import uuidutils

from esi_leap.common import statuses
from esi_leap.manager.service import ManagerService
from esi_leap.objects import contract
from esi_leap.objects import offer


lessee_ctx = ctx.RequestContext(project_id="lesseeid",
                                roles=['lessee'])
owner_ctx = ctx.RequestContext(project_id='ownerid',
                               roles=['owner'])

o_uuid = uuidutils.generate_uuid()

test_offer = offer.Offer(
    resource_type='test_node',
    resource_uuid='abc',
    name="o",
    uuid=o_uuid,
    status=statuses.AVAILABLE,
    start_time=datetime.datetime(3000, 7, 16),
    end_time=datetime.datetime(4000, 7, 16),
    project_id=owner_ctx.project_id
)

test_contract = contract.Contract(
    offer_uuid=o_uuid,
    name='c',
    uuid=uuidutils.generate_uuid(),
    project_id=lessee_ctx.project_id,
    status=statuses.CREATED,
    start_time=datetime.datetime(3000, 7, 16),
    end_time=datetime.datetime(4000, 7, 16),
)


@mock.patch('esi_leap.manager.service.timeutils.utcnow')
@mock.patch('esi_leap.manager.service.LOG.info')
@mock.patch('esi_leap.manager.service.contract.Contract.get_all')
def test__fulfill_contracts(mock_ga, mock_log, mock_utcnow):
    mock_ga.return_value = [test_contract]
    mock_utcnow.return_value = datetime.datetime(3500, 7, 16)

    s = ManagerService()

    with mock.patch.object(test_contract, 'fulfill') as mock_fulfill:
        s._fulfill_contracts()

        mock_fulfill.assert_called_once()

    mock_ga.assert_called_once()
    mock_log.assert_called_once()


@mock.patch('esi_leap.manager.service.timeutils.utcnow')
@mock.patch('esi_leap.manager.service.LOG.info')
@mock.patch('esi_leap.manager.service.contract.Contract.get_all')
def test__expire_contracts(mock_ga, mock_log, mock_utcnow):
    mock_ga.return_value = [test_contract]
    mock_utcnow.return_value = datetime.datetime(3500, 7, 16)

    s = ManagerService()

    with mock.patch.object(test_contract, 'expire') as mock_expire:
        s._expire_contracts()

        mock_expire.assert_called_once()

    mock_ga.assert_called_once()
    mock_log.assert_called_once()


@mock.patch('esi_leap.manager.service.timeutils.utcnow')
@mock.patch('esi_leap.manager.service.LOG.info')
@mock.patch('esi_leap.manager.service.offer.Offer.get_all')
def test__expire_offers(mock_ga, mock_log, mock_utcnow):
    mock_ga.return_value = [test_offer]
    mock_utcnow.return_value = datetime.datetime(3500, 7, 16)

    s = ManagerService()

    with mock.patch.object(test_offer, 'expire') as mock_expire:
        s._expire_offers()

        mock_expire.assert_called_once()

    mock_ga.assert_called_once()
    mock_log.assert_called_once()
