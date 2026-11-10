#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Usage: ./bin/build_rust.sh <NAME> <GITREPO> <GITREV> <REVDATE>
#
# Builds a rust program, putting the binary in build/bin/ and a version file in
# build/.
#
# Note: This should be called from inside a container.

set -euo pipefail

NAME=$1
GITREPO=$2
GITREV=$3
REVDATE=$4

# Print versions for debugging
rustc -vV

# Build the specific version we want
echo ">>> compiling ${NAME} rev ${GITREV} ${REVDATE} ..."
cargo install --locked \
    --target=x86_64-unknown-linux-gnu \
    --root=./build/ \
    --git $GITREPO \
    --rev $GITREV \
    --profile release \
    --force \
    $NAME

# Capture some data about it in a .json file
echo "{\"sha\":\"$GITREV\",\"date\":\"$REVDATE\"}" > ./build/$NAME.version.json
