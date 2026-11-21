#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Usage: ./bin/generate_regression_data.py [CRASHIDFILE]

This runs minidump-stackwalk and/or symbolicate-stacks on a set of crash ids
generating rough regression test data. You run it on a set of crash ids before
and after a change and then look at how things changed.
"""

from abc import ABC, abstractmethod
import datetime
import os
import pathlib
import shutil
import subprocess
import tempfile
import textwrap
import time
import typing

import click


SYMBOLS_CACHE = pathlib.Path("symbols_cache")
SYMBOLS_URL = "https://symbols.mozilla.org"
NUM_TIMES = 5


class ProcessError(Exception):
    pass


def get_raw_crash_path(crashdata_dir, crashid):
    return f"{crashdata_dir}/raw_crash/20{crashid[-6:]}/{crashid}"


def get_dump_path(crashdata_dir, crashid):
    return f"{crashdata_dir}/upload_file_minidump/{crashid}"


def fetch_data(crashdata_dir, crashid, need_dumps):
    """Fetch raw crash and minidump from Crash Stats."""
    raw_crash = get_raw_crash_path(crashdata_dir, crashid)
    dump = get_dump_path(crashdata_dir, crashid)

    if os.path.exists(raw_crash) and os.path.exists(dump):
        click.echo(f"Already fetched {raw_crash} and {dump}")
        return

    args = [
        "fetch-data",
        "--raw",
    ] + (["--dumps"] if need_dumps else []) + [
        crashdata_dir,
        crashid,
    ]

    ret = subprocess.run(args, capture_output=True)
    stdout = ret.stdout.decode("utf-8")
    stderr = ret.stderr.decode("utf-8")
    if ret.returncode != 0:
        raise ProcessError(f"fetch-data: stdout: {stdout} stderr: {stderr}")
    click.echo(stdout)


def symbolscache_size(symbolscache):
    """Return size of symbols cache directory in bytes."""
    return sum(
        os.path.getsize(os.path.join(root, file))
        for root, dirs, files in os.walk(symbolscache)
        for file in files
    )


class Test(ABC):
    def __init__(self, regr_dir, label):
        self.label = label
        self.output_dir = regr_dir / self.label
        self.output_dir.mkdir(exist_ok=True)
        self.timing_file = self.output_dir / "timings.csv"
        self.exe = pathlib.Path("build", "bin", self.binary).absolute().resolve()

        if not self.exe.exists():
            click.echo(
                f"{self.exe} does not exist. Please build it first.",
            )
            click.get_current_context().exit(1)

    class Instance(ABC):
        def __init__(self, test, crashid):
            self.test = test
            self.crashid = crashid
            # The tests we currently use output json, so create an output file for them.
            self.output_file = self.test.output_dir / f"output.{self.crashid}.json"

        @abstractmethod
        def loop_setup(self):
            pass

        @abstractmethod
        def loop_run(self):
            pass

        @abstractmethod
        def finish(self, row):
            pass

        def run(self):
            row = [self.crashid]
            for i in range(NUM_TIMES):
                click.echo(f"{self.test.label} ({i+1}/{NUM_TIMES}) ... ", nl=False)
                self.loop_setup()

                start_time = time.time()
                self.loop_run()
                end_time = time.time()
                delta = int(end_time - start_time)

                click.echo(f"{delta}s")
                row.append(delta)

            self.finish(row)

            row = [str(item) for item in row]
            click.echo(",".join(row))
            with open(str(self.test.timing_file), "a") as fp:
                fp.write(",".join(row) + "\n")

    def create(self, crashid) -> type[Test.Instance]:
        return self.__class__.Instance(self, crashid)


class StackwalkerTest(Test):
    binary = "minidump-stackwalk"

    def __init__(self, regr_dir, crashdata_dir, cache):
        super().__init__(regr_dir, "stackwalker_cache" if cache else "stackwalker_nocache")
        self.cache = cache
        self.symbolscache = SYMBOLS_CACHE
        self.symbolsurl = SYMBOLS_URL
        self.crashdata_dir = crashdata_dir

    class Instance(Test.Instance):
        def loop_setup(self):
            if not self.test.cache:
                shutil.rmtree(self.test.symbolscache, ignore_errors=True)
                self.test.symbolscache.mkdir()
                (self.test.symbolscache / "tmp").mkdir()
                (self.test.symbolscache / "cache").mkdir()

        def loop_run(self):
            raw_crash = get_raw_crash_path(self.test.crashdata_dir, self.crashid)
            dump = get_dump_path(self.test.crashdata_dir, self.crashid)

            ret = subprocess.run(
                [
                    str(self.test.exe),
                    f"--evil-json={raw_crash}",
                    f"--symbols-cache={self.test.symbolscache}/cache",
                    f"--symbols-tmp={self.test.symbolscache}/tmp",
                    "--no-color",
                    f"--symbols-url={self.test.symbolsurl}",
                    f"--output-file={self.output_file}",
                    "--json",
                    "--verbose=error",
                    dump,
                ],
                capture_output=True,
            )

            if ret.returncode != 0:
                stdout = ret.stdout.decode("utf-8")
                stderr = ret.stderr.decode("utf-8")
                raise ProcessError(f"stackwalker: stdout: {stdout} stderr: {stderr}")

        def finish(self, row):
            # Append symbols cache size
            row.append(str(symbolscache_size(str(self.test.symbolscache))))
            # Append output size
            row.append(self.output_file.stat().st_size)
            # Append output file
            row.append(str(self.output_file))


class SymbolicateTest(Test):
    binary = "symbolicate-stacks"

    def __init__(self, regr_dir, crashdata_dir, cache):
        super().__init__(regr_dir, "symbolicate_cache" if cache else "symbolicate_nocache")
        self.symbolscache = SYMBOLS_CACHE
        self.crashdata_dir = crashdata_dir
        self.cache = cache

    class Instance(Test.Instance):
        def loop_setup(self):
            if not self.test.cache:
                shutil.rmtree(self.test.symbolscache, ignore_errors=True)

        def loop_run(self):
            annotations = get_raw_crash_path(self.test.crashdata_dir, self.crashid)
            ret = subprocess.run(
                [
                    str(self.test.exe),
                    f"--input-file={annotations}",
                    f"--output-file={self.output_file}",
                    f"""symbol_servers.breakpad = ["{SYMBOLS_URL}"]""",
                    f"""symbol_servers.windows = ["{SYMBOLS_URL}"]""",
                    f"""cache.directory = "{self.test.symbolscache}" """,
                ],
                capture_output=True,
            )

            if ret.returncode != 0:
                stdout = ret.stdout.decode("utf-8")
                stderr = ret.stderr.decode("utf-8")
                raise ProcessError(f"symbolicate-stacks: stdout: {stdout} stderr: {stderr}")

        def finish(self, row):
            # Append symbols cache size
            row.append(str(symbolscache_size(str(self.test.symbolscache))))
            # Append output size
            row.append(self.output_file.stat().st_size)
            # Append output file
            row.append(str(self.output_file))


def process_crashid(
    tests: list[Test], crashid
):
    """Processes a crashid generating test data."""
    for test in tests:
        test.create(crashid).run()


@click.command()
@click.option("--binary",
    multiple=True,
    default="all",
    help="The binaries to test. May be specified zero or more times.",
    type=click.Choice([StackwalkerTest.binary,SymbolicateTest.binary]),
    show_default=True
)
@click.argument("crashidfile", type=click.Path(exists=True))
@click.pass_context
def main(ctx, binary, crashidfile):
    if "CRASHSTATS_API_TOKEN" not in os.environ:
        click.echo("You need to define CRASHSTATS_API_TOKEN in the environment.")
        ctx.exit(1)

    now = datetime.datetime.now()

    regr_root = pathlib.Path("regr")
    regr_dir = regr_root / now.strftime("%Y%m%d_%H%M%S")
    regr_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Using {regr_dir}")

    crashdata_dir = regr_root / "crashdata"
    crashdata_dir.mkdir(parents=True, exist_ok=True)

    # The ordering of tests here is important for correct behavior: for the
    # stackwalker tests and symbolicate tests, we run the `cache=False` tests
    # first, and the `cache=True` tests will start with a populated cache from
    # the prior test run (as desired).
    #
    # The symbolicate no-cache tests are run first after the stackwalker tests
    # so that we can take advantage of it clearing the cache (its use of the
    # cache dir may be different than that of the stackwalker).
    tests = [
        StackwalkerTest(
            regr_dir=regr_dir,
            crashdata_dir=crashdata_dir,
            cache=False,
        ),
        StackwalkerTest(
            regr_dir=regr_dir,
            crashdata_dir=crashdata_dir,
            cache=True,
        ),
        SymbolicateTest(
            regr_dir=regr_dir,
            crashdata_dir=crashdata_dir,
            cache=False,
        ),
        SymbolicateTest(
            regr_dir=regr_dir,
            crashdata_dir=crashdata_dir,
            cache=True,
        ),
    ]

    # Filter out tests based on `--binary`
    tests = [t for t in tests if t.binary in binary]
    need_dumps = StackwalkerTest.binary in binary

    with open(crashidfile, "r") as fp:
        crashids = fp.readlines()

    for crashid in crashids:
        if "#" in crashid:
            crashid = crashid[: crashid.find("#")]
        crashid = crashid.strip()
        if not crashid:
            continue

        click.echo(f">>> Working on {crashid} ...")
        fetch_data(crashdata_dir=str(crashdata_dir), crashid=crashid, need_dumps=need_dumps)

        try:
            process_crashid(tests, crashid)
        except ProcessError as exc:
            click.echo(f"error: {exc!r}")

        click.echo("")


if __name__ == "__main__":
    main()
