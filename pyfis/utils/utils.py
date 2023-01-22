"""
Copyright (C) 2021-2023 Julian Metzler

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import csv
import itertools


def _debug_print(debug, *args, **kwargs):
    if debug:
        print(*args, **kwargs)

def debug_hex(message, readable_ascii = False, readable_ctrl = False):
    """
    Turn a message into a readable form
    """

    CTRL_CHARS = {
        0x02: "STX",
        0x03: "ETX",
        0x04: "EOT",
        0x05: "ENQ",
        0x10: "DLE",
        0x15: "NAK",
        0x17: "ETB"
    }

    result = []
    for byte in message:
        if readable_ctrl and byte in CTRL_CHARS:
            result.append(CTRL_CHARS[byte])
        elif readable_ascii and byte not in range(0, 32) and byte != 127:
            result.append(chr(byte))
        else:
            result.append("{:02X}".format(byte))
    return " ".join(result)


def vias_in_route(route, vias):
    # Check if the given vias are all present in the given route in the right order
    # If an entry in vias is a list, all of its items will be considered to be aliases of each other
    i = 0
    j = 0
    while i < len(route) and j < len(vias):
        if type(vias[j]) in (tuple, list):
            for alias in vias[j]:
                if route[i] == alias:
                    j += 1
                    break
        else:
            if route[i] == vias[j]:
                j += 1
        i += 1
    return j == len(vias)


def get_vias(route, weights, *via_groups, check_dashes=True, debug=False):
    # Get the ideal combination of vias based on split-flap modules
    num_groups = len(via_groups)
    
    # Go through all via groups and take note of possible candidates
    via_candidates = []
    for group in via_groups:
        group_candidates = []
        for pos, entry in group.items():
            if vias_in_route(route, entry['stations']):
                group_candidates.append(pos)
        via_candidates.append(group_candidates)
    _debug_print(debug, "Via candidates:")
    _debug_print(debug, via_candidates)
    
    # Check all combinations to see if the order makes sense
    combinations = itertools.product(*via_candidates)
    valid_combinations = []
    _debug_print(debug, "\nVia candidates with sensible order:")
    for combination in combinations:
        stations = []
        for group, pos in enumerate(combination):
            stations.extend(via_groups[group][pos]['stations'])
        if vias_in_route(route, stations):
            _debug_print(debug, combination, stations)
            valid_combinations.append(combination)
    
    # If check_dashes is True, check if the starts and endings are compatible,
    # i.e. if the first segment ends on a dash, the next one
    # cannot start with one.
    if check_dashes:
        valid_dash_combinations = []
        _debug_print(debug, "\nCandidates after check_dashes:")
        for combination in valid_combinations:
            valid = True
            prev_text = None
            for group, pos in enumerate(combination):
                text = via_groups[group][pos]['text'].strip()
                if group > 0:
                    if prev_text and text and prev_text.endswith("-") == text.startswith("-"):
                        _debug_print(debug, "Excluded: ", prev_text, text)
                        valid = False
                        break
                prev_text = text
            if valid:
                _debug_print(debug, combination)
                valid_dash_combinations.append(combination)
        valid_combinations = valid_dash_combinations

    # Build the texts of all valid combinations
    # and remove combinations that contain double entries
    final_combinations = []
    for combination in valid_combinations:
        text_stations = []
        for group, pos in enumerate(combination):
            text_stations.extend([s.strip() for s in via_groups[group][pos]['text'].split(" - ") if s.strip()])
        if len(set(text_stations)) == len(text_stations):
            # No double entries detected
            final_combinations.append([combination, text_stations])
    
    # Calculate the total weight of each combinations
    for i, entry in enumerate(final_combinations):
        combination, text_stations = entry
        weight = 0
        for text_station in text_stations:
            weight += weights.get(text_station, 1)
        final_combinations[i].append(weight)
    final_combinations.sort(key=lambda c: c[2], reverse=True)

    _debug_print(debug, "\nFinal combinations (Score, Positions, Text):")
    for entry in final_combinations:
        _debug_print(debug, entry[2], entry[0], " - ".join(entry[1]))
    _debug_print(debug, "")
    
    if final_combinations:
        return final_combinations[0][0]
    else:
        return None

def vias_from_csv(filename):
    # Build the dict required for get_vias from a CSV file
    vias = {}
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')
        for i, row in enumerate(reader):
            if i == 0 or not row[1]:
                continue
            vias[int(row[0])] = {
                'text': row[1],
                'stations': [[subentry.strip() for subentry in entry.split(",")] for entry in row[2:] if entry]
            }
    return vias

def map_from_csv(filename):
    # Build the dict required for SplitFlapDisplay from a CSV file.
    # CSV format: column 0 = flap position, column 1 = destination as printed on the flap
    _map = {}
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')
        for i, row in enumerate(reader):
            if i == 0 or not row[1]:
                continue
            _map[int(row[0])] = row[1]
    return _map

def alternatives_map_from_csv(filename):
    # Build the dict required for an alternative station name mapping from a CSV file.
    # CSV format: column 0 = flap position (irrelevant), column 1 = destination as printed on the flap,
    # column 2 = comma separated list of alternative station names that map to this flap
    _map = {}
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')
        for i, row in enumerate(reader):
            if i == 0 or not row[1]:
                continue
            for station_name in row[2].split(","):
                if station_name.strip() and station_name.strip() != row[1]:
                    _map[station_name.strip()] = row[1]
    return _map
