#!/usr/bin/env bash

cd "$(git rev-parse --show-toplevel)"
pycodestyle $(./ci/list_tracked_pyfiles.sh)
