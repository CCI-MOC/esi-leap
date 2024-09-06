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

"""
Adapted from Nova
"""

import hashlib

from oslo_config import cfg
from oslo_db.exception import DBDuplicateEntry
from oslo_log import log as logging
from oslo_utils import timeutils
from oslo_utils import uuidutils
from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.common import exception
from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def get_sha256_str(base_str):
    base_str = base_str.encode("utf-8")
    return hashlib.sha256(base_str).hexdigest()


@versioned_objects_base.VersionedObjectRegistry.register
class ConsoleAuthToken(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        "id": fields.IntegerField(),
        "node_uuid": fields.UUIDField(nullable=False),
        "token": fields.StringField(nullable=False),
        "expires": fields.IntegerField(nullable=False),
    }

    @property
    def access_url_base(self):
        return "ws://%s:%s" % (
            CONF.serialconsoleproxy.host_address,
            CONF.serialconsoleproxy.port,
        )

    @property
    def access_url(self):
        if self.obj_attr_is_set("id"):
            return "%s/?token=%s" % (self.access_url_base, self.token)

    def authorize(self, ttl):
        if self.obj_attr_is_set("id"):
            raise exception.TokenAlreadyAuthorized()

        token = uuidutils.generate_uuid()
        token_hash = get_sha256_str(token)
        expires = timeutils.utcnow_ts() + ttl

        updates = self.obj_get_changes()
        if "token" in updates:
            del updates["token"]
        updates["token_hash"] = token_hash
        updates["expires"] = expires

        try:
            db_obj = dbapi.console_auth_token_create(updates)
            db_obj["token"] = token
            self._from_db_object(self._context, self, db_obj)
        except DBDuplicateEntry:
            raise exception.TokenAlreadyAuthorized()

        LOG.debug(
            "Authorized token with expiry %(expires)s for node %(node)s",
            {"expires": expires, "node": self.node_uuid},
        )
        return token

    @classmethod
    def validate(cls, token, context=None):
        token_hash = get_sha256_str(token)
        db_obj = dbapi.console_auth_token_get_by_token_hash(token_hash)

        if db_obj is not None:
            db_obj["token"] = token
            obj = cls._from_db_object(context, cls(), db_obj)
            LOG.debug("Validated token for node %(node)s", {"node": obj.node_uuid})
            return obj
        else:
            LOG.debug("Token validation failed")
            raise exception.InvalidToken()

    @classmethod
    def clean_console_tokens_for_node(cls, node_uuid):
        dbapi.console_auth_token_destroy_by_node_uuid(node_uuid)

    @classmethod
    def clean_expired_console_tokens(cls):
        dbapi.console_auth_token_destroy_expired()
