#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Usage: ./bin/generate_regression_data.py [CRASHIDFILE]

This runs minidump-stackwalk on a set of crash ids generating rough regression
test data. You run it on a set of crash ids before and after a change and then
look at how things changed.
"""

import datetime
import os
import pathlib
import subprocess
import time

import click


SYMBOLS_CACHE = pathlib.Path("symbols_cache")
STACKWALKER = pathlib.Path("build", "bin", "minidump-stackwalk")
SYMBOLS_URL = "https://symbols.mozilla.org"
NUM_TIMES = 5


class ProcessError(Exception):
    pass


def get_raw_crash_path(crashdata_dir, crashid):
    return f"{crashdata_dir}/raw_crash/20{crashid[-6:]}/{crashid}"


def get_dump_path(crashdata_dir, crashid):
    return f"{crashdata_dir}/upload_file_minidump/{crashid}"


def fetch_data(crashdata_dir, crashid):
    """Fetch raw crash and minidump from Crash Stats."""
    raw_crash = get_raw_crash_path(crashdata_dir, crashid)
    dump = get_dump_path(crashdata_dir, crashid)

    if os.path.exists(raw_crash) and os.path.exists(dump):
        click.echo(f"Already fetched {raw_crash} and {dump}")
        return

    ret = subprocess.run(
        [
            "fetch-data",
            "--raw",
            "--dumps",
            crashdata_dir,
            crashid,
        ],
        capture_output=True,
    )
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


def run_mdsw(
    stackwalker, crashdata_dir, symbolsurl, symbolscache, output_file, crashid
):
    """Runs stackwalker on crash data."""
    raw_crash = get_raw_crash_path(crashdata_dir, crashid)
    dump = get_dump_path(crashdata_dir, crashid)

    ret = subprocess.run(
        [
            str(stackwalker),
            f"--evil-json={raw_crash}",
            f"--symbols-cache={symbolscache}/cache",
            f"--symbols-tmp={symbolscache}/tmp",
            "--no-color",
            f"--symbols-url={symbolsurl}",
            f"--output-file={output_file}",
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


def process_crashid(
    stackwalker, regr_dir, crashdata_dir, symbolsurl, symbolscache, crashid
):
    """Processes a crashid generating test data."""
    output_dir = regr_dir / "nocache"
    output_dir.mkdir(exist_ok=True)
    timing_file = output_dir / "timings.csv"
    output_file = output_dir / f"output.{crashid}.json"

    row = [crashid]

    # Run stackwalker and append times
    for i in range(NUM_TIMES):
        click.echo(f"nocache ({i+1}/{NUM_TIMES}) ... ", nl=False)
        subprocess.run(["rm", "-rf", str(symbolscache)])
        symbolscache.mkdir()
        (symbolscache / "tmp").mkdir()
        (symbolscache / "cache").mkdir()

        start_time = time.time()
        run_mdsw(
            stackwalker=str(stackwalker),
            crashdata_dir=str(crashdata_dir),
            symbolsurl=symbolsurl,
            symbolscache=str(symbolscache),
            output_file=str(output_file),
            crashid=crashid,
        )
        end_time = time.time()
        delta = int(end_time - start_time)
        click.echo(f"{delta}s")
        row.append(str(delta))

    # Append symbols cache size
    row.append(str(symbolscache_size(str(symbolscache))))

    # Append output size
    row.append(output_file.stat().st_size)

    # Append output file
    row.append(str(output_file))

    row = [str(item) for item in row]
    click.echo(",".join(row))
    with open(str(timing_file), "a") as fp:
        fp.write(",".join(row) + "\n")

    # Now do it all again with the cache
    output_dir = regr_dir / "cache"
    output_dir.mkdir(exist_ok=True)
    timing_file = output_dir / "timings.csv"
    output_file = output_dir / f"output.{crashid}.json"

    row = [crashid]

    # Run stackwalker and append times
    for i in range(NUM_TIMES):
        click.echo(f"cache ({i+1}/{NUM_TIMES}) ... ", nl=False)
        start_time = time.time()
        run_mdsw(
            stackwalker=str(stackwalker),
            crashdata_dir=str(crashdata_dir),
            symbolsurl=symbolsurl,
            symbolscache=str(symbolscache),
            output_file=str(output_file),
            crashid=crashid,
        )
        end_time = time.time()
        delta = int(end_time - start_time)
        click.echo(f"{delta}s")
        row.append(str(delta))

    # Append symbols cache size
    row.append(str(symbolscache_size(str(symbolscache))))

    # Append output size
    row.append(output_file.stat().st_size)

    # Append output file
    row.append(str(output_file))

    row = [str(item) for item in row]
    click.echo(",".join(row))
    with open(str(timing_file), "a") as fp:
        fp.write(",".join(row) + "\n")


@click.command()
@click.argument("crashidfile", type=click.Path(exists=True))
@click.pass_context
def main(ctx, crashidfile):
    stackwalker = STACKWALKER.absolute().resolve()

    if not stackwalker.exists():
        click.echo(
            f"Stackwalker {stackwalker} does not exist. Please build it first.",
        )
        ctx.exit(1)

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

    with open(crashidfile, "r") as fp:
        crashids = fp.readlines()

    for crashid in crashids:
        if "#" in crashid:
            crashid = crashid[: crashid.find("#")]
        crashid = crashid.strip()
        if not crashid:
            continue

        click.echo(f">>> Working on {crashid} ...")
        fetch_data(crashdata_dir=str(crashdata_dir), crashid=crashid)

        try:
            process_crashid(
                stackwalker=stackwalker,
                regr_dir=regr_dir,
                crashdata_dir=crashdata_dir,
                symbolsurl=SYMBOLS_URL,
                symbolscache=SYMBOLS_CACHE,
                crashid=crashid,
            )
        except ProcessError as exc:
            click.echo(f"stackwalker error: {exc!r}")

        click.echo("")


if __name__ == "__main__":
    main()
