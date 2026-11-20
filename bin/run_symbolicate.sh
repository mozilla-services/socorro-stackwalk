#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Usage: ./bin/run_symbolicate.sh [CRASHID]
#
# This runs symbolicate-stacks just like it runs in the crash ingestion
# processor. This will help debug symbolication problems.

set -euo pipefail

DATADIR=./crashdata_tmp
SYMBOLICATE="./build/bin/symbolicate-stacks"
SYMBOLSCACHE="./symbols_cache"

# This will pull symbols from the symbols server
SYMBOLS_URL="https://symbols.mozilla.org/try"

CONFIG_FILE="$(mktemp --suffix _symbolicate-stacks-config)"
trap 'rm -rf -- "$CONFIG_FILE"' EXIT

cat << EOF > "$CONFIG_FILE"
[symbol_servers]
breakpad = ["${SYMBOLS_URL}"]
windows = ["${SYMBOLS_URL}"]

[cache]
directory = "${SYMBOLSCACHE}"
EOF

if [[ $# -eq 0 ]]; then
    if [ -t 0 ]; then
        # If stdin is a terminal, then there's no input
        echo "Usage: run_symbolicate.sh CRASHID"
        exit 1
    fi

    # stdin is not a terminal, so pull the args from there
    set -- ${@:-$(</dev/stdin)}
fi

hash fetch-data 2>/dev/null || { echo >&2 "fetch-data is not installed. Run 'pip install crashstats-tools'. Exiting."; exit 1; }

mkdir "${DATADIR}" || true

findcrash() {
    local CRASHID
    CRASHID=$1
    find "${DATADIR}/raw_crash/" -name "${CRASHID}" -type f
}

for CRASHID in "$@"
do
    # Pull down the data for the crash if we don't have it yet.
    if [ -z "$(findcrash ${CRASHID})" ]; then
        echo "Fetching crash data..."
        fetch-data --raw "${DATADIR}" "${CRASHID}"
    fi

    RAWCRASHFILE=$(findcrash ${CRASHID})

    "${SYMBOLICATE}" \
        --config-file="${CONFIG_FILE}" \
        --input-file="${RAWCRASHFILE}" \
        --output-file="${CRASHID}.dump.json"
done
