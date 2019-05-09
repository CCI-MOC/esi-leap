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

# borrowed from Ironic

from wsme import types as wtypes


class Collection(wtypes.Base):

    next = wtypes.text

    @property
    def collection(self):
        return getattr(self, self._type)

    def has_next(self, limit):
        """Return whether collection has more items."""
        return len(self.collection) and len(self.collection) == limit

    def get_next(self, limit, url=None, **kwargs):
        if not self.has_next(limit):
            return wtypes.Unset

        url = url or self._type
        q_args = ''.join(['%s=%s&' % (key, kwargs[key]) for key in kwargs])
        next_args = '?%(args)slimit=%(limit)d&marker=%(marker)s' % {
            'args': q_args, 'limit': limit,
            'marker': getattr(self.collection[-1], 'uuid')}

        next_link = "%(url)s/v1/%(resource)s%(args)s" % {
            'url': url,
            'resource': self._type,
            'args': next_args
        }

        return next_link
