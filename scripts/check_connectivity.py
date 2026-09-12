#!/usr/bin/env python3
"""Compare PCB pin groups with a KiCad XML netlist, ignoring generated net names.

Requires KiCad's pcbnew Python module. Export the netlist with:
    kicad-cli sch export netlist --format kicadxml -o /tmp/hdmi2c.xml hdmi2c.kicad_sch

An optional baseline netlist verifies that removing specified components leaves
all other pin connections unchanged. This checks assigned nets, not physical
routing or clearances; run KiCad DRC separately.
"""

import argparse
from collections import defaultdict
import sys
import xml.etree.ElementTree as ET

import pcbnew


def schematic_groups(path, removed=()):
    root = ET.parse(path)
    groups = set()
    for net in root.findall("./nets/net"):
        pins = frozenset(
            (node.attrib["ref"], node.attrib["pin"])
            for node in net.findall("node")
            if node.attrib["ref"] not in removed
        )
        if pins:
            groups.add(pins)
    if not groups:
        raise ValueError(f"No pin groups found in {path}")
    return groups


def compare(label, expected, actual):
    if expected == actual:
        print(f"PASS: {label} ({len(actual)} pin groups)")
        return True
    print(f"FAIL: {label}")
    for description, groups in (("Missing", expected - actual), ("Unexpected", actual - expected)):
        for group in sorted(sorted(pins) for pins in groups):
            print(f"  {description}: {group}")
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board")
    parser.add_argument("netlist")
    parser.add_argument("--baseline-netlist")
    parser.add_argument("--removed", nargs="*", default=[])
    args = parser.parse_args()
    if args.removed and not args.baseline_netlist:
        parser.error("--removed requires --baseline-netlist")

    board = pcbnew.LoadBoard(args.board)
    if board is None:
        raise ValueError(f"Could not load {args.board}")
    nets = defaultdict(set)
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname():
                nets[pad.GetNetname()].add((footprint.GetReference(), pad.GetNumber()))
    actual = set(map(frozenset, nets.values()))
    expected = schematic_groups(args.netlist)
    ok = compare("PCB matches schematic connectivity", expected, actual)
    if args.baseline_netlist:
        baseline = schematic_groups(args.baseline_netlist, set(args.removed))
        ok = compare("Retained schematic connections match baseline", baseline, expected) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
