#!/usr/bin/env python3

from collections import defaultdict
import sys
import json

from bs4 import BeautifulSoup


def parse(filehandle):
    # takes unparsed html from http://192.168.100.1/cmSignalData.htm
    # returns dict[title:string][channel:int][value:string] => float
    soup = BeautifulSoup(filehandle, 'html.parser')

    measurements = defaultdict(lambda: defaultdict(dict))

    tables = [c.table for c in soup.html.body.find_all('center')]

    for table in tables[0:1]: # FIXME remove range
        (header, id_row, *rows) = table.tbody.find_all('tr', recursive=False)
        title = header.th.get_text()
        ids = [ int(cell.get_text()) for cell in id_row.find_all('td')[1:] ]
        for row in rows:
            for cell in row.find_all('td', recursive=False):
                if cell.table:
                    cell.table.extract() # remove stupid refresh note

            (field, *values) = [ cell.string.strip() for cell in row.find_all('td') ]
            for (the_id, value) in zip(ids, values):
                measurements[title][the_id][field] = value
    return measurements


# main
if len(sys.argv) == 1:
    print("Usage: {} FILE1 [FILE2 ...]".format(sys.argv[0]))

for filename in sys.argv[1:]:
    with open(filename) as ff:
        values = parse(ff)
        print(json.dumps(values, indent=4, sort_keys=True))
