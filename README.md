# README

This is the repository for building rust-minidump minidump-stackwalk for
Socorro.


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

If you have [crashstats-tools](https://pypi.org/project/crashstats-tools/) installed and a `CRASHSTATS_API_TOKEN`, then you can test your stackwalk binary with `bin/run_mdsw.sh CRASHID`.


# Submitting bugs

Don't submit bugs here--this is just a repository for building a binary for using in Socorro.

Submit bugs in the [rust-minidump repo](https://github.com/rust-minidump/rust-minidump).
