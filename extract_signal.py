#!/usr/bin/env python3

from collections import defaultdict
import sys
import json
import argparse

from bs4 import BeautifulSoup


def parse(filehandle):
    # takes unparsed html from http://192.168.100.1/cmSignalData.htm
    # returns dict[title:string][channel:int][value:string] => float
    soup = BeautifulSoup(filehandle, "html.parser")

    measurements = defaultdict(lambda: defaultdict(dict))

    tables = [c.table for c in soup.html.body.find_all("center")]

    for table in tables:
        (header, id_row, *rows) = table.tbody.find_all("tr", recursive=False)
        title = header.th.get_text()
        ids = [int(cell.get_text()) for cell in id_row.find_all("td")[1:]]
        for row in rows:
            for cell in row.find_all("td", recursive=False):
                if cell.table:
                    cell.table.extract()  # remove stupid refresh note

            (field, *values) = [cell.get_text().strip() for cell in row.find_all("td")]
            for (the_id, value) in zip(ids, values):
                measurements[title][the_id][field] = value
    return measurements


def main():
    parser = argparse.ArgumentParser(
        description="Parse and emit surfboard signal status."
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        type=argparse.FileType('r'),
        nargs="+",
        help="saved HTTP responses to process",
    )

    args = parser.parse_args()
    for fh in args.files:
        values = parse(fh)
        print(json.dumps(values, indent=4, sort_keys=True))


if __name__ == "__main__":
    main()
