# README

This is the repository for building
[minidump-stackwalk](https://github.com/rust-minidump/rust-minidump) and
[symbolicate-stacks](https://github.com/mozilla/symbolicate-stacks) tools for
[Socorro](https://github.com/mozilla-services/socorro).


# Building

## With docker:

1. `make build` builds the Docker container for building
2. `make shell` gets you into a shell in the Docker container
3. `bin/build_release.sh` builds the tools and puts a release in `releases/`

## Without docker:

1. `bin/build_release.sh` builds the tools and puts a release in `releases/`


# Using

Once you've built the tools, you can use them. They'll be in `build/bin/`.

There are wrapper scripts that run the binaries (and require [API access](#API)):
- run the stackwalker with `bin/run_mdsw.sh CRASHID`
- run the symbolicator with `bin/run_symbolicate.sh CRASHID`


## API
Running the wrapper scripts and the regression tests both require that you have
[crashstats-tools](https://pypi.org/project/crashstats-tools/) installed and a
`CRASHSTATS_API_TOKEN` env variable set to a token that has the "View Raw Dumps" and "View Personal
Identifiable Information" permissions.


# Submitting bugs

Submit bugs for the socorro-stackwalker build and test scripts in
[bugzilla](https://bugzilla.mozilla.org/enter_bug.cgi?format=__standard__&product=Socorro&component=General).

Submit bugs for the stackwalker in the [rust-minidump
repo](https://github.com/rust-minidump/rust-minidump/issues).

Submit bugs for the symbolicator in the [symbolicate-stacks
repo](https://github.com/mozilla/symbolicate-stacks/issues).


# Submitting patches

All changes must be approved by a code owner.

Patches are manually verified and tested. At some point, we will change this.


# Regression testing

Regression testing requires [API access](#API).

Create a Python virtual environment and install the requirements from
`requirements-dev.txt`.

To regression test changes:

1. Build the tools with the main branch.

2. Build a file consisting of crash ids from Crash Stats. Run `supersearch --num=20 >
   crashids.txt` with the following additional flags to `supersearch`:

   - For testing reports with a minidump but no `StackTraces` (always able to be processed by the
     stackwalker): `--crash_report_keys=upload_file_minidump`
   - For testing reports with potentially no minidump and `StackTraces` (always able to be processed
     by the symbolicator): `--crash_report_keys=StackTraces`
   - For a mix, include both of the above flags (they combine as a binary OR). This set of crashes
     will be able to be meaningfully processed by the stackwalker, the symbolicator, or both.

3. Run regression tests on it:

   ```
   $ ./bin/generate_regression_data.py crashids.txt
   ```

   This takes 30-40 minutes to run.

4. Make the changes to the tools (version updates, patches, etc).

5. Run regression tests on it again. Again, it takes 30-40 minutes to run.

6. Compare timings and sizes.

   ```
   $ ./bin/regression_stats.py regr/<FIRSTDIR> regr/<SECONDDIR>
   ```


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
   $ make shell
   (in container)$ ./bin/build_release.sh
   ```
   The .tar.gz file is now in `releases/` directory.
3. Push tag to github:
   ```
   $ git push --tags REMOTE main
   ```
4. Make a release on github and upload the release .tar.gz file.
