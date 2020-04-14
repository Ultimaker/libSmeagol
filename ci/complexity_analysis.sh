#!/bin/sh

set -eu

# TODO set limits, shouldn't expect 100%
lizard -Eduplicate libSmeagol || true

exit 0
