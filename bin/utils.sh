#!/bin/bash
set -euo pipefail

# Get the commit date of a given commit (defaulting to HEAD)
# The first argument is the path to the git checkout.
# The second argument is an optional ref.
git-commit-date() {
    local DIR
    DIR=$1
    shift
    git -C $DIR show --no-patch --format=%cd --date=short "$@"
}
