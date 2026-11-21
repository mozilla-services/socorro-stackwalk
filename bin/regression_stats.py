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
        crashid, *timings, cache_size, output_size, output_file = line.strip().split(",")
        return cls(
            crashid=crashid,
            times=[int(t) for t in timings],
            cache_size=int(cache_size),
            output_size=int(output_size),
            output_file=output_file,
        )

    def best_time(self):
        return min(self.times)


def load_timings(d):
    timings_file = os.path.join(d, "timings.csv")
    with open(timings_file, "r") as fp:
        return [Timing.from_line(line) for line in fp]


def print_timings(d):
    for timing in load_timings(d):
        click.echo(
            f"{timing.crashid} -> "
            + f"{timing.best_time()}s  "
            + f"cache:{timing.cache_size:,}b  "
            + f"output:{timing.output_size:,}b"
        )


def stats_regr(d):
    subdirs = (f for f in os.listdir(d) if os.path.isdir(os.path.join(d, f)))
    for sd in subdirs:
        click.echo(f"{sd} timings")
        print_timings(os.path.join(d, sd))
        click.echo("")


def compare_regr(d1, d2):
    console = Console()

    d1_subdirs = set(f for f in os.listdir(d1) if os.path.isdir(os.path.join(d1, f)))
    d2_subdirs = set(f for f in os.listdir(d2) if os.path.isdir(os.path.join(d2, f)))

    subdirs = d1_subdirs & d2_subdirs

    def str_and_colorize(left_side, right_side):
        """If both are same--no color. If both are different--yellow."""
        if left_side != right_side:
            return (
                f"[yellow]{left_side:,}[/yellow]",
                f"[yellow]{right_side:,}[/yellow]",
            )
        else:
            return (f"{left_side:,}", f"{right_side:,}")

    for sd in subdirs:
        d1_timings = load_timings(os.path.join(d1, sd))
        d2_timings = load_timings(os.path.join(d2, sd))

        d1_by_crash = {timing.crashid: timing for timing in d1_timings}
        d2_by_crash = {timing.crashid: timing for timing in d2_timings}

        table = Table(title = sd, show_edge=False, show_header=True, show_lines=False, box=None)
        table.add_column("crashid")

        table.add_column("run1 best time")
        table.add_column("cache size")
        table.add_column("output size")

        table.add_column("run2 best time")
        table.add_column("cache size")
        table.add_column("output size")

        for key in d1_by_crash.keys():
            if key not in d2_by_crash:
                click.echo(f"{key} not in {sd} timings right side")
                continue

            timing1 = d1_by_crash[key]
            timing2 = d2_by_crash[key]

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
