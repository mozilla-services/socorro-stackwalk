#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Usage: ./bin/build_stackwalker.sh
#
# Builds the stackwalker, puts binary in build/bin/, and creates a release
# .tar.gz file.
#
# Note: This should be called from inside a container.

set -euo pipefail

# From: https://github.com/rust-minidump/rust-minidump
MINIDUMPREV=v0.16.0
MINIDUMPREVDATE=2023-04-27

TARFILE="socorro-stackwalker.${MINIDUMPREVDATE}.${MINIDUMPREV}.tar.gz"

# Print versions for debugging
rustc -vV

# Build the specific version we want of minidump-stackwalk
echo ">>> compiling minidump-stackwalk sha ${MINIDUMPREV} ${MINIDUMPREVDATE} ..."
cargo install --locked \
    --target=x86_64-unknown-linux-gnu \
    --root=./build/ \
    --git https://github.com/rust-minidump/rust-minidump.git \
    --rev $MINIDUMPREV \
    --profile release \
    --force \
    minidump-stackwalk

# Capture some data about it in a .json file
echo "{\"sha\":\"$MINIDUMPREV\",\"date\":\"$MINIDUMPREVDATE\"}" > ./build/stackwalk.version.json

# Print all that out to make sure it looks right
find ./build -type f -exec 'ls' '-l' '{}' ';'

# Create the tar file for the GitHub release page
echo ">>> creating tarfile ..."
mkdir -p releases || true
tar -czvf "releases/${TARFILE}" ./build/bin/ ./build/stackwalk.version.json

echo ">>> tarfile data ..."
tar -tzvf "releases/${TARFILE}"
ls -l ./releases/
