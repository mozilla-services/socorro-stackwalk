#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Usage: ./bin/run_mdsw.sh [CRASHID]
#
# This runs minidump-stackwalk just like it runs in the crash ingestion
# processor. This will help debug stackwalk problems.

set -euo pipefail

DATADIR=./crashdata_mdsw_tmp
STACKWALKER="./build/bin/minidump-stackwalk"

# This will pull symbols from the symbols server
SYMBOLS="--symbols-url=https://symbols.mozilla.org"
SYMBOLS_CACHE="./symbols_cache"

# This will pull symbols from disk
# SYMBOLS="--symbols-path=/app/symbols/

if [[ $# -eq 0 ]]; then
    if [ -t 0 ]; then
        # If stdin is a terminal, then there's no input
        echo "Usage: run_mdsw.sh CRASHID"
        exit 1
    fi

    # stdin is not a terminal, so pull the args from there
    set -- ${@:-$(</dev/stdin)}
fi

hash fetch-data 2>/dev/null || { echo >&2 "fetch-data is not installed. Run 'pip install crashstats-tools'. Exiting."; exit 1; }

mkdir "${DATADIR}" || true
mkdir "${SYMBOLS_CACHE}" || true

for CRASHID in "$@"
do
    # Pull down the data for the crash if we don't have it, yet
    if [ ! -f "${DATADIR}/v1/dump/${CRASHID}" ]; then
        echo "Fetching crash data..."
        fetch-data --raw --dumps "${DATADIR}" "${CRASHID}"
    fi

    # Find the raw crash file
    RAWCRASHFILE=$(find "${DATADIR}/raw_crash/" -name "${CRASHID}" -type f)

    timeout -s KILL 600 "${STACKWALKER}" \
        --evil-json="${RAWCRASHFILE}" \
        --symbols-cache="${SYMBOLS_CACHE}/cache" \
        --symbols-tmp="${SYMBOLS_CACHE}/tmp" \
        --no-color \
        "${SYMBOLS}" \
        --json \
        --verbose=error \
        "${DATADIR}/upload_file_minidump/${CRASHID}"
done
