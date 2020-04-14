#!/bin/sh

set -eu

vulture --min-confidence 100 "libSmeagol"

exit 0
