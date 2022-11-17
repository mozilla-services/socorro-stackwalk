# README

This is the repository for building rust-minidump minidump-stackwalk for
[Socorro](https://github.com/mozilla-services/socorro).


# Building

## With docker:

1. `make build` builds the Docker container for building
2. `make shell` gets you into a shell in the Docker container
3. `bin/build_stackwalker.sh` builds stackwalker and puts a release in `releases/`

## Without docker:

1. `bin/build_stackwalker.sh` builds stackwalker and puts a release in `releases/`


# Using

Once you've built stackwalker, you can use it. It'll be in
`build/bin/minidump-stackwalk`.

If you have [crashstats-tools](https://pypi.org/project/crashstats-tools/)
installed and a `CRASHSTATS_API_TOKEN`, then you can test your stackwalk binary
with `bin/run_mdsw.sh CRASHID`.


# Submitting bugs

Don't submit bugs here--this is just a repository for building a binary for
using in Socorro.

Submit bugs in the [rust-minidump repo](https://github.com/rust-minidump/rust-minidump).


# Submitting patches

All changes must be approved by a code owner.

Patches are manually verified and tested. At some point, we will change this.


# Release

1. Tag main tip:
   ```
   $ git tag -s vYYYYMMDD.N
   ```
   For example:
   ```
   $ git tag -s v20220803.0
   ```
   In tag comment include link to rust-minidump sha or tag.

   For example:
   ```
   v20220830.0

   This is the initial packaging for rust-minidump for Socorro. It's
   f9933c36 which corresponds with the v0.14.0 release.

   https://github.com/rust-minidump/rust-minidump/releases/tag/0.14.0
   ```
2. Build release:
   ```
   $ make clean
   $ make build
   ```
3. Push tag to github:
   ```
   $ git push --tags REMOTE main
   ```
4. Make a release on github and upload the release .tar.gz file.
