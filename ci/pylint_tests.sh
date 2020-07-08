#!/usr/bin/env bash

cd "$(git rev-parse --show-toplevel)"
pylint \
  --disable=all \
  --enable=undefined-variable \
  --enable=unused-variable \
  --enable=unused-import \
  --enable=wildcard-import \
  --enable=signature-differs \
  --enable=arguments-differ \
  --enable=logging-not-lazy \
  --enable=reimported \
  $(./ci/list_tracked_pyfiles.sh)
