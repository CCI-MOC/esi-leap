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

from datetime import datetime

import mock

from esi_leap.tests.api import base as test_api_base


class FakeIronicNode(object):
    def __init__(self):
        self.name = "fake-node"
        self.owner = "fake-project-uuid"
        self.uuid = "fake-uuid"
        self.properties = {"lease_uuid": "fake-lease-uuid", "cpu": "40"}
        self.lessee = "fake-project-uuid"
        self.maintenance = False
        self.provision_state = "active"
        self.target_provision_state = "target_state"
        self.power_state = "power off"
        self.target_power_state = "power on"
        self.resource_class = "baremetal"


class FakeProject(object):
    def __init__(self):
        self.name = "fake-project"
        self.id = "fake-project-uuid"


class FakeOffer(object):
    def __init__(self, uuid, start_time, end_time):
        self.uuid = uuid
        self.resource_uuid = "fake-uuid"
        self.start_time = start_time
        self.end_time = end_time


class FakeFutureLease(object):
    def __init__(self):
        self.uuid = "fake-future-lease-uuid"
        self.resource_uuid = "fake-uuid"


class TestNodesController(test_api_base.APITestCase):
    def setUp(self):
        super(TestNodesController, self).setUp()

    @mock.patch("esi_leap.common.ironic.get_node_list")
    @mock.patch("esi_leap.objects.offer.Offer.get_all")
    @mock.patch("esi_leap.objects.lease.Lease.get_all")
    @mock.patch("esi_leap.common.keystone.get_project_list")
    def test_get_all(self, mock_gpl, mock_lga, mock_oga, mock_gnl):
        fake_node = FakeIronicNode()
        fake_project = FakeProject()
        fake_offer = FakeOffer(
            "fake-offer-uuid", start_time=datetime.min, end_time=datetime.max
        )
        fake_future_offer = FakeOffer(
            "fake-future-offer-uuid", start_time=datetime.max, end_time=datetime.max
        )
        fake_future_lease = FakeFutureLease()
        mock_gnl.return_value = [fake_node]
        mock_oga.return_value = [fake_offer, fake_future_offer]
        mock_lga.return_value = [fake_future_lease]
        mock_gpl.return_value = [fake_project]

        data = self.get_json("/nodes")

        mock_gnl.assert_called_once_with(self.context)
        mock_oga.assert_called_once()
        mock_lga.assert_called_once()
        mock_gpl.assert_called_once()

        self.assertEqual(data["nodes"][0]["name"], "fake-node")
        self.assertEqual(data["nodes"][0]["uuid"], "fake-uuid")
        self.assertEqual(data["nodes"][0]["owner"], "fake-project")
        self.assertEqual(data["nodes"][0]["lease_uuid"], "fake-lease-uuid")
        self.assertEqual(data["nodes"][0]["lessee"], "fake-project")
        self.assertEqual(data["nodes"][0]["properties"], {"cpu": "40"})
        self.assertEqual(data["nodes"][0]["offer_uuid"], "fake-offer-uuid")
        self.assertEqual(data["nodes"][0]["lease_uuid"], "fake-lease-uuid")
        self.assertEqual(data["nodes"][0]["future_offers"], ["fake-future-offer-uuid"])
        self.assertEqual(data["nodes"][0]["future_leases"], ["fake-future-lease-uuid"])

    @mock.patch("esi_leap.common.ironic.get_node_list")
    @mock.patch("esi_leap.common.keystone.get_project_list")
    def test_get_all_resource_class_filter(self, mock_gpl, mock_gnl):
        fake_node = FakeIronicNode()
        fake_project = FakeProject()
        mock_gnl.return_value = [fake_node]
        mock_gpl.return_value = [fake_project]

        data = self.get_json("/nodes?resource_class=baremetal")

        mock_gnl.assert_called_once_with(self.context, resource_class="baremetal")
        mock_gpl.assert_called_once()

        self.assertEqual(data["nodes"][0]["resource_class"], "baremetal")

    @mock.patch("esi_leap.common.ironic.get_node_list")
    @mock.patch("esi_leap.common.keystone.get_project_list")
    @mock.patch("esi_leap.common.keystone.get_project_uuid_from_ident")
    def test_get_all_owner_filter(self, mock_get_project_uuid, mock_gpl, mock_gnl):
        fake_node = FakeIronicNode()
        fake_project = FakeProject()
        mock_gnl.return_value = [fake_node]
        mock_gpl.return_value = [fake_project]

        mock_get_project_uuid.return_value = fake_project.id

        data = self.get_json("/nodes?owner=fake-project")

        mock_gnl.assert_called_once_with(self.context, owner=fake_project.id)
        mock_get_project_uuid.assert_called_once_with("fake-project")

        self.assertEqual(data["nodes"][0]["owner"], fake_project.name)

    @mock.patch("esi_leap.common.ironic.get_node_list")
    @mock.patch("esi_leap.common.keystone.get_project_list")
    @mock.patch("esi_leap.common.keystone.get_project_uuid_from_ident")
    def test_get_all_lesse_filter(self, mock_get_project_uuid, mock_gpl, mock_gnl):
        fake_node = FakeIronicNode()
        fake_project = FakeProject()
        mock_gnl.return_value = [fake_node]
        mock_gpl.return_value = [fake_project]

        mock_get_project_uuid.return_value = fake_project.id

        data = self.get_json("/nodes?lessee=fake-project")

        mock_gnl.assert_called_once_with(self.context, lessee=fake_project.id)
        mock_get_project_uuid.assert_called_once_with("fake-project")

        self.assertEqual(data["nodes"][0]["lessee"], "fake-project")
