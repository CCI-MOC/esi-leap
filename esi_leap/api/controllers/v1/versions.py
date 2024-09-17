# Copyright (c) 2015 Intel Corporation
# All Rights Reserved.
#
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

# Borrowed from Ironic

# This is the version 1 API
BASE_VERSION = 1

# Here goes a short log of changes in every version.
# Refer to docs/esi-leap-api-version-history.md for a detailed
# explanation of what each version contains.
#
# v1.0: API at the point in time when versioning support was added.

MINOR_0_INITIAL_VERSION = 0

# When adding another version, update:
# - MINOR_MAX_VERSION
# - docs/esi-leap-api-version-history.md with a detailed
#   explanation of what changed in the new version

MINOR_MAX_VERSION = MINOR_0_INITIAL_VERSION

# String representations of the minor and maximum versions
_MIN_VERSION_STRING = "{}.{}".format(BASE_VERSION, MINOR_0_INITIAL_VERSION)
_MAX_VERSION_STRING = "{}.{}".format(BASE_VERSION, MINOR_MAX_VERSION)


def min_version_string():
    """Returns the minimum supported API version (as a string)"""
    return _MIN_VERSION_STRING


def max_version_string():
    """Returns the maximum supported API version (as a string)."""
    return _MAX_VERSION_STRING
