#!/usr/bin/env python3

from collections import defaultdict
import sys
import itertools
import os
import re
import json
import argparse
import csv

from bs4 import BeautifulSoup

TIMESTAMP_KEY = "timestamp"
MAX_CHANNEL = 40


def parse(filehandle):
    # takes unparsed html from http://192.168.100.1/cmSignalData.htm
    # returns dict[title:string][channel:int][value:string] => str
    soup = BeautifulSoup(filehandle, "html.parser")

    measurements = defaultdict(lambda: defaultdict(dict))

    tables = [c.table for c in soup.html.body.find_all("center")]

    for table in tables:
        (header, id_row, *rows) = table.tbody.find_all("tr", recursive=False)
        title = header.th.get_text().strip()
        ids = [int(cell.get_text()) for cell in id_row.find_all("td")[1:]]
        for row in rows:
            for cell in row.find_all("td", recursive=False):
                if cell.table:
                    cell.table.extract()  # remove stupid refresh note

            (field, *values) = [cell.get_text().strip() for cell in row.find_all("td")]
            for (the_id, value) in zip(ids, values):
                measurements[title][the_id][field] = value
    return measurements


def flatten_measurement(measurements):
    # flattens a dict[title:string][channel:int][value:string] => str
    # as returned by parse into a dict[$TITLE-$VALUE-$CHANNEL:str] => str
    row = {}
    for title, table in measurements.items():
        if isinstance(table, dict):
            field_names = set(
                list(
                    itertools.chain(*[list(fields.keys()) for fields in table.values()])
                )
            )
            for the_id in range(1, MAX_CHANNEL + 1):
                for field in field_names:
                    try:
                        value = table[the_id][field]
                    except KeyError:
                        value = ""
                    row["{}-{}-{:02d}".format(title, field, the_id)] = value
        else:
            row[title] = table  # timestamp, etc.
    return row


def main():
    parser = argparse.ArgumentParser(
        description="Parse and emit surfboard signal status."
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        type=argparse.FileType("r"),
        nargs="+",
        help="saved HTTP responses to process",
    )
    parser.add_argument(
        "--timestamp",
        "-t",
        choices=["metadata", "filename", "none"],
        default="metadata",
        help="source of time in each record",
    )

    parser.add_argument(
        "--output-format",
        "-o",
        choices=["json", "csv"],
        default="json",
        help="structured output format",
    )

    args = parser.parse_args()
    csvwriter = None
    for fh in args.files:
        values = parse(fh)
        timestamp = None
        if args.timestamp == "metadata":
            timestamp = int(os.path.getmtime(fh.name))
        elif args.timestamp == "filename":
            match = re.search("\\d+", fh.name)
            if not match:
                raise Exception(
                    "Unable to extract timestamp number from filename: {}".format(
                        fh.name
                    )
                )
            timestamp = int(match.group(0))
        if timestamp is not None:
            values[TIMESTAMP_KEY] = timestamp
        if args.output_format == "json":
            print(json.dumps(values, indent=4, sort_keys=True))
        elif args.output_format == "csv":
            row = flatten_measurement(values)
            if csvwriter is None:
                csvwriter = csv.DictWriter(
                    sys.stdout,
                    fieldnames=[TIMESTAMP_KEY]
                    + list(filter(lambda x: (x != TIMESTAMP_KEY), sorted(row.keys()))),
                )
                csvwriter.writeheader()
            csvwriter.writerow(row)


if __name__ == "__main__":
    main()
