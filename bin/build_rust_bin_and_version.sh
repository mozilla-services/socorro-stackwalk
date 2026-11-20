#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Usage: ./bin/build_rust.sh <GIT_REPO> <GIT_REV> <BIN_NAME> 
#
# Builds a rust program, putting the binary named BIN_NAME from
# GIT_REPO@GIT_REV in build/bin/ and a version file in build/.
#
# Note: This should be called from inside a container.

set -euo pipefail

source $(dirname $0)/utils.sh

GIT_REPO=$1
GIT_REV=$2
BIN_NAME=$3

# Print versions for debugging
rustc -vV

# Fetch the repo to a temp directory (to get the revision date from git history)
echo ">>> fetching ${BIN_NAME} rev ${GIT_REV} ..."

CHECKOUT=$(mktemp -d)
trap 'rm -rf -- "$CHECKOUT"' EXIT
# Shallow clone the requested revision
# advice.detachedHead=false silences the unnecessary warning about a detached HEAD
git -c advice.detachedHead=false clone --quiet --depth 1 --revision $GIT_REV $GIT_REPO $CHECKOUT

# Derive the rev date from the commit information
REV_DATE=$(git-commit-date $CHECKOUT)

# minidump-stackwalk is a subcrate within rust-minidump. This is a bit of a
# hack because `cargo install --path` doesn't resolve virtual (workspace)
# manifests intelligently. `cargo install --git=file:///THE_PATH` actually does
# work, but cargo creates another copy of the repo, so it's a bit ugly, too.
CRATE_PATH=$CHECKOUT
if [ -e "$CHECKOUT/$BIN_NAME" ]; then
    CRATE_PATH="$CHECKOUT/$BIN_NAME"
fi

# Build this version of the program
echo ">>> compiling ${BIN_NAME} rev ${GIT_REV} (${REV_DATE}) ..."
cargo install --locked \
    --path=$CRATE_PATH \
    --target=x86_64-unknown-linux-gnu \
    --root=./build/ \
    --profile release \
    --force \
    $BIN_NAME

# Capture some data about it in a .json file
echo "{\"sha\":\"$GIT_REV\",\"date\":\"$REV_DATE\"}" > ./build/$BIN_NAME.version.json
