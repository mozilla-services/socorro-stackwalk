#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Usage: ./bin/build_release.sh
#
# Builds the binaries, puts artifacts in build/, and creates a release
# .tar.gz file.
#
# Note: This should be called from inside a container.

set -euo pipefail

DIR=$(dirname $0)

source $DIR/utils.sh

# From: https://github.com/rust-minidump/rust-minidump
MINIDUMP_REV=v0.27.0

# From: https://github.com/mozilla/symbolicate-stacks
SYMBOLICATE_REV=0.3.0

if [ -n "$(git status --porcelain)" ]; then
    >&2 echo "working directory not clean: refusing to create release"
    exit 1
fi

$DIR/build_rust_bin_and_version.sh https://github.com/rust-minidump/rust-minidump.git $MINIDUMP_REV minidump-stackwalk 
$DIR/build_rust_bin_and_version.sh https://github.com/mozilla/symbolicate-stacks.git $SYMBOLICATE_REV symbolicate-stacks 

RELEASE_REV=$(git rev-parse --short HEAD)
RELEASE_DATE=$(git-commit-date .)

TARFILE="socorro-stackwalker-${RELEASE_REV}.${RELEASE_DATE}.tar.gz"

# Print everything out to make sure it looks right
find ./build -type f -exec 'ls' '-l' '{}' ';'

# Create the tar file for the GitHub release page
echo ">>> creating tarfile ..."
mkdir -p releases || true
tar -czvf "releases/${TARFILE}" ./build/bin/ ./build/*.version.json

echo ">>> tarfile data ..."
tar -tzvf "releases/${TARFILE}"
ls -l ./releases/
