#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Usage: ./bin/build_release.sh
#
# Builds the binaries, puts artifacts in in build/, and creates a release
# .tar.gz file.
#
# Note: This should be called from inside a container.

set -euo pipefail

# From: https://github.com/rust-minidump/rust-minidump
MINIDUMPREV=v0.27.0
MINIDUMPREVDATE=2026-08-11

# From: https://github.com/mozilla/symbolicate-stacks
SYMBOLICATEREV=0.2.0
SYMBOLICATEREVDATE=2026-10-02

./bin/build_rust.sh minidump-stackwalk https://github.com/rust-minidump/rust-minidump.git $MINIDUMPREV $MINIDUMPREVDATE
./bin/build_rust.sh symbolicate-stacks https://github.com/mozilla/symbolicate-stacks.git $SYMBOLICATEREV $SYMBOLICATEREVDATE

DATE=$(date +%F)

TARFILE="socorro-stackwalker.${DATE}.tar.gz"

# Print everything out to make sure it looks right
find ./build -type f -exec 'ls' '-l' '{}' ';'

# Create the tar file for the GitHub release page
echo ">>> creating tarfile ..."
mkdir -p releases || true
tar -czvf "releases/${TARFILE}" ./build/bin/ ./build/*.version.json

echo ">>> tarfile data ..."
tar -tzvf "releases/${TARFILE}"
ls -l ./releases/
