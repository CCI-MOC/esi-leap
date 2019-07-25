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

from esi_leap.common import statuses
from esi_leap.objects import flocx_market_client
from esi_leap.objects import offer
import json
from keystoneauth1 import adapter
from keystoneauth1 import loading as ks_loading
from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def get_flocx_market_client():
    auth_plugin = ks_loading.load_auth_from_conf_options(
        CONF, 'flocx_market')
    sess = ks_loading.load_session_from_conf_options(CONF, 'flocx_market',
                                                     auth=auth_plugin)
    adpt = adapter.Adapter(
        session=sess,
        service_type='marketplace',
        interface='public')
    return flocx_market_client.FlocxMarketClient(adpt)


def retrieve_from_flocx_market(context):
    marketplace_client = get_flocx_market_client()
    contract_list = get_contracts(context, marketplace_client)
    return contract_list


def get_contracts(context, marketplace_client):
    contracts = []
    contract_offer_list = get_ocr_by_status(marketplace_client)
    if len(contract_offer_list) == 0:
        return []
    for contract_offer in contract_offer_list:
        contract_data = {}
        contract_id = contract_offer["contract_id"]
        marketplace_offer_id = contract_offer["marketplace_offer_id"]
        ocr_id = contract_offer["offer_contract_relationship_id"]
        contract_data["marketplace_offer_contract_relationship_id"] = ocr_id
        c = get_contract_by_id(contract_id, marketplace_client)
        contract_data["start_date"] = c["start_time"]
        contract_data["end_date"] = c["end_time"]
        contract_data["status"] = statuses.OPEN
        bid = get_bid_by_id(c["bid_id"], marketplace_client)
        contract_data["project_id"] = bid["project_id"]
        offer_marketplace = get_offer_by_id(
            marketplace_offer_id, marketplace_client)
        provider_offer_id = offer_marketplace["provider_offer_id"]
        offer_provider = offer.Offer.get(context, provider_offer_id).to_dict()
        contract_data["offer_uuid"] = provider_offer_id
        contract_data["properties"] = offer_provider["properties"]
        contracts.append(contract_data)
    return contracts


def get_ocr_by_status(marketplace_client):
    url = CONF.flocx_market.endpoint_override + \
        '/offer_contract_relationship?status=unretrieved'
    r = marketplace_client.get(url)
    if r.status_code != 200:
        LOG.warning(
            "Failed to retrieve contracts from flocx-market. Got HTTP %s: %s",
            r.status_code,
            r.text)
        return []
    if r.content is not None:
        return json.loads(r.content)
    else:
        return []


def get_contract_by_id(contract_id, marketplace_client):
    url = CONF.flocx_market.endpoint_override + '/contract/' + contract_id
    res = marketplace_client.get(url)
    return json.loads(res.content)


def get_bid_by_id(bid_id, marketplace_client):
    url = CONF.flocx_market.endpoint_override + '/bid/' + bid_id
    res = marketplace_client.get(url)
    return json.loads(res.content)


def get_offer_by_id(offer_id, marketplace_client):
    url = CONF.flocx_market.endpoint_override + '/offer/' + offer_id
    res = marketplace_client.get(url)
    return json.loads(res.content)


def update_contract(o_c_r_id, marketplace_client):
    url = CONF.flocx_market.endpoint_override + \
        '/offer_contract_relationship/' + o_c_r_id
    data = {"status": "retrieved"}
    r = marketplace_client.put(url, data)
    if r.status_code != 200:
        LOG.warning(
            "Failed to update a contract to flocx-market. Got HTTP %s: %s",
            r.status_code,
            r.text)
    return r.status_code


def update_flocx_market_contract(o_c_r_id):
    marketplace_client = get_flocx_market_client()
    res_status_code = update_contract(o_c_r_id, marketplace_client)
    return res_status_code
