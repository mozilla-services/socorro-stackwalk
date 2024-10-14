#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Either displays data for a single regression run or compares two regression
runs.
"""

import dataclasses
import os
import sys

import click
from rich.console import Console
from rich.table import Table

USAGE = "regression_stats.py [DIR1] <[DIR2]>"


@dataclasses.dataclass
class Timing:
    crashid: str
    times: list[int]
    cache_size: int
    output_size: int
    output_file: str

    @classmethod
    def from_line(cls, line):
        crashid, t1, t2, t3, t4, t5, cache_size, output_size, output_file = line
        return cls(
            crashid=crashid,
            times=[int(t) for t in [t1, t2, t3, t4, t5]],
            cache_size=int(cache_size),
            output_size=int(output_size),
            output_file=output_file,
        )

    def best_time(self):
        return min(self.times)


def stats_regr(d):
    if d.endswith(os.path.sep):
        d = d.rstrip(os.path.sep)

    click.echo("nocache_timings")
    nocache_stats = f"{d}/nocache/timings.csv"
    with open(nocache_stats, "r") as fp:
        nocache_timings = [Timing.from_line(line.strip().split(",")) for line in fp]

    for timing in nocache_timings:
        click.echo(
            f"{timing.crashid} -> "
            + f"{timing.best_time()}s  "
            + f"cache:{timing.cache_size:,}b  "
            + f"output:{timing.output_size:,}b"
        )

    click.echo("")

    click.echo("cache_timings")
    cache_stats = f"{d}/cache/timings.csv"
    with open(cache_stats, "r") as fp:
        cache_timings = [Timing.from_line(line.strip().split(",")) for line in fp]

    for timing in cache_timings:
        click.echo(
            f"{timing.crashid} -> "
            + f"{timing.best_time()}s  "
            + f"cache:{timing.cache_size:,}kb  "
            + f"output:{timing.output_size:,}b"
        )


def compare_regr(d1, d2):
    console = Console()

    if d1.endswith(os.path.sep):
        d1 = d1.rstrip(os.path.sep)

    if d2.endswith(os.path.sep):
        d2 = d2.rstrip(os.path.sep)

    nocache_stats1 = f"{d1}/nocache/timings.csv"
    with open(nocache_stats1, "r") as fp:
        timings = [Timing.from_line(line.strip().split(",")) for line in fp]
        nocache_timings1 = {timing.crashid: timing for timing in timings}

    nocache_stats2 = f"{d2}/nocache/timings.csv"
    with open(nocache_stats2, "r") as fp:
        timings = [Timing.from_line(line.strip().split(",")) for line in fp]
        nocache_timings2 = {timing.crashid: timing for timing in timings}

    table = Table(show_edge=False, show_header=True, show_lines=False, box=None)
    table.add_column("crashid")

    table.add_column("run1 best time")
    table.add_column("cache size")
    table.add_column("output size")

    table.add_column("run2 best time")
    table.add_column("cache size")
    table.add_column("output size")

    def str_and_colorize(left_side, right_side):
        """If both are same--no color. If both are different--yellow."""
        if left_side != right_side:
            return (
                f"[yellow]{left_side:,}[/yellow]",
                f"[yellow]{right_side:,}[/yellow]",
            )
        else:
            return (f"{left_side:,}", f"{right_side:,}")

    for key in nocache_timings1.keys():
        if key not in nocache_timings2:
            click.echo(f"{key} not in nocache timings right")
            continue

        timing1 = nocache_timings1[key]
        timing2 = nocache_timings2[key]

        row = [key]
        pairs = [
            str_and_colorize(timing1.best_time(), timing2.best_time()),
            str_and_colorize(timing1.cache_size, timing2.cache_size),
            str_and_colorize(timing1.output_size, timing2.output_size),
        ]

        for i in range(len(pairs[0])):
            for j in range(len(pairs)):
                row.append(pairs[j][i])

        table.add_row(*row)

    console.print(table)


@click.command()
@click.argument("run", nargs=-1)
@click.pass_context
def main(ctx, run):
    if len(run) == 1:
        stats_regr(run[0])

    elif len(run) == 2:
        compare_regr(run[0], run[1])

    else:
        click.echo(ctx.get_usage())
        sys.exit(1)


if __name__ == "__main__":
    main()
