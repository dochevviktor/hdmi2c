#!/usr/bin/env python3
"""Check the rev2 carrier's electrical contract and mounting geometry.

Requires KiCad's pcbnew module. Pass a freshly exported KiCad XML netlist.
This complements ERC/DRC; it does not validate electronics on physical hardware.
Optional --seeed-footprints compares lands with the downloaded official library.
"""

import argparse
from collections import defaultdict
import hashlib
from pathlib import Path
import sys

import pcbnew as k

from check_connectivity import compare, schematic_groups


ROOT = Path(__file__).resolve().parents[1]
XIAO_MODEL = "3d/Seeed_Studio_XIAO_ESP32C6.step"
XIAO_MODEL_SHA256 = "2e1ce01f4497192485823ca9fffd68e323bafc84cd7b85c2906b5497550be8fc"


# Reviewed against Seeed V1.0 and TI's PW (not RKT) package pin table.
CONNECTIONS = {
    "VBUS": "U3.14 U4.11 C1.1",
    "+3V3": "U3.12 U4.24 C2.1 R26.1 R27.1",
    "GND": "U3.13 U4.6 U4.14 U4.19 J7.2 J7.5 J7.8 J7.11 J7.17 J7.SH "
           "C1.2 C2.2 C3.2 R24.2 R25.2 SW2.2 SW3.2 TP2.1",
    "HDMI_5V_EN": "U3.1 U4.12 R24.1",
    "DDC_EN": "U3.2 U4.5 R25.1",
    "HDMI_HPD": "U3.3 U4.4",
    "I2C_SDA": "U3.5 U4.3",
    "I2C_SCL": "U3.6 U4.2",
    "BUTTON1": "U3.9 SW2.1 R26.2",
    "BUTTON2": "U3.10 SW3.1 R27.2",
    "HDMI_SCL": "U4.8 J7.15 TP3.1",
    "HDMI_SDA": "U4.9 J7.16 TP4.1",
    "HDMI_HPD_5V": "U4.10 J7.19",
    "HDMI_5V": "U4.13 J7.18 C3.1 TP1.1",
}
UNCONNECTED = {
    "U3": "4 7 8 11",
    "U4": "1 7 15 16 17 18 20 21 22 23",
    "J7": "1 3 4 6 7 9 10 12 13 14",
}
VALUES = {
    "U3": "XIAO ESP32-C6", "U4": "TPD12S016PWR", "J7": "HDMI1",
    "C1": "100nF", "C2": "100nF", "C3": "100nF",
    "R24": "100k", "R25": "100k", "R26": "10k", "R27": "10k",
    "SW2": "B3U-1000P", "SW3": "B3U-1000P",
    "TP1": "HDMI_5V", "TP2": "GND", "TP3": "SCL_5V", "TP4": "SDA_5V",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def mm_pair(vector):
    return tuple(round(k.ToMM(value), 6) for value in vector)


def lands(footprint):
    return {
        pad.GetNumber(): (mm_pair(pad.GetPosition() - footprint.GetPosition()),
                          mm_pair(pad.GetSize()))
        for pad in footprint.Pads()
    }


def check_xiao_model(footprint):
    models = list(footprint.Models())
    require(len(models) == 1, "XIAO must have exactly one detailed 3D model")
    model = models[0]
    require(model.m_Filename == "${KIPRJMOD}/" + XIAO_MODEL and model.m_Show,
            "XIAO 3D model must be visible and project-relative")
    for field, expected in (("m_Offset", (15.0014, 8.759341, .25)),
                            ("m_Rotation", (-90, 0, -90)), ("m_Scale", (1, 1, 1))):
        vector = getattr(model, field)
        actual = (vector.x, vector.y, vector.z)
        require(all(abs(a - b) < 1e-6 for a, b in zip(actual, expected)),
                f"XIAO 3D model {field} changed: {actual}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board")
    parser.add_argument("netlist")
    parser.add_argument("--seeed-footprints", type=Path)
    args = parser.parse_args()
    board = k.LoadBoard(args.board)
    require(board is not None, "Cannot load board")
    feet = {foot.GetReference(): foot for foot in board.GetFootprints()}
    require(len(list(board.GetFootprints())) == len(VALUES), "Duplicate or extra footprint")
    require(set(feet) == set(VALUES), "Unexpected components or legacy circuitry")
    for ref, value in VALUES.items():
        require(feet[ref].GetValue() == value, f"Unexpected value for {ref}")
        expected_layer = k.B_Cu if ref.startswith("TP") else k.F_Cu
        require(feet[ref].GetLayer() == expected_layer, f"Wrong assembly side: {ref}")

    nets = defaultdict(set)
    for ref, foot in feet.items():
        for pad in foot.Pads():
            nets[pad.GetNetname().lstrip("/")].add((ref, pad.GetNumber()))
    for name, connections in CONNECTIONS.items():
        expected = {tuple(pin.split(".")) for pin in connections.split()}
        require(nets[name] == expected, f"Unexpected connections on {name}: {nets[name]}")
    expected_groups = {frozenset(tuple(pin.split(".")) for pin in pins.split())
                       for pins in CONNECTIONS.values()}
    expected_groups.update(frozenset({(ref, pin)}) for ref, pins in UNCONNECTED.items()
                           for pin in pins.split())
    actual_groups = set(map(frozenset, nets.values()))
    require(compare("Rev2 electrical contract", expected_groups, actual_groups), "Pin contract failed")
    require(compare("Schematic matches PCB", schematic_groups(args.netlist), actual_groups), "Parity failed")
    for ref, pins in UNCONNECTED.items():
        for pad in feet[ref].Pads():
            if pad.GetNumber() in pins.split():
                require("no_connect" in pad.GetPinType(), f"Missing intentional NC: {ref}.{pad.GetNumber()}")
    require(feet["U4"].GetFPID().GetLibItemName() == "TSSOP-24_4.4x7.8mm_P0.65mm",
            "U4 must use the PW/TSSOP-24 package")

    require(abs(feet["U3"].GetOrientationDegrees()) < .001, "Rev2 XIAO orientation changed")
    expected_lands = {}
    for num in range(1, 15):
        row = num - 1 if num <= 7 else 14 - num
        expected_lands[str(num)] = ((.835 if num <= 7 else 17.0, round(-18.12 + 2.54 * row, 6)), (2.75, 2.0))
    require(lands(feet["U3"]) == expected_lands, "XIAO pad geometry/numbering changed")
    if args.seeed_footprints:
        source = k.FootprintLoad(str(args.seeed_footprints), "XIAO-ESP32-C6-SMD")
        require(source is not None, "Cannot load official Seeed footprint")
        source_lands = {pin: geometry for pin, geometry in lands(source).items() if int(pin) <= 14}
        require(source_lands == expected_lands, "Downloaded Seeed lands differ from reviewed snapshot")
        print("PASS: All 14 castellation lands match the official Seeed library")
    print("PASS: 14-pad XIAO mounting pattern; no underside test/battery lands")

    model_path = ROOT / XIAO_MODEL
    require(model_path.is_file(), "Missing local XIAO STEP file")
    require(hashlib.sha256(model_path.read_bytes()).hexdigest() == XIAO_MODEL_SHA256,
            "XIAO STEP differs from the reviewed snapshot; repeat the mechanical review")
    check_xiao_model(feet["U3"])
    library_footprint = k.FootprintLoad(str(ROOT / "hdmi2c.pretty"), "XIAO_ESP32C6_Castellated")
    require(library_footprint is not None, "Cannot load local XIAO footprint")
    check_xiao_model(library_footprint)
    print("PASS: Pinned XIAO STEP and reviewed transform in PCB and footprint library")

    outline = k.SHAPE_POLY_SET()
    require(board.GetBoardPolygonOutlines(outline, False), "Invalid board outline")
    box = outline.BBox()
    require(abs(k.ToMM(box.GetWidth()) - 42) < .001 and abs(k.ToMM(box.GetHeight()) - 24) < .001,
            "Carrier bounding box is not 42 x 24 mm")
    require(board.GetCopperLayerCount() == 2, "Expected two copper layers")
    require(abs(k.ToMM(board.GetDesignSettings().GetBoardThickness()) - 1.6) < .001,
            "Expected 1.6 mm board thickness")
    # Check the safety rule areas themselves; DRC checks actual copper against them.
    keepouts = {z.GetZoneName(): z for z in board.Zones() if z.GetIsRuleArea()}
    wanted = {
        "XIAO underside: no carrier copper, vias or pads":
            ({k.F_Cu}, [(54.5, 50.2), (67.3, 50.2), (67.3, 66.2), (54.5, 66.2)]),
        "XIAO antenna: all-layer copper keepout":
            ({k.F_Cu, k.B_Cu}, [(54.5, 66.2), (67.3, 66.2), (67.3, 74.5), (54.5, 74.5)]),
    }
    for name, (layers, points) in wanted.items():
        require(name in keepouts, f"Missing safety keepout: {name}")
        zone = keepouts[name]
        require(set(zone.GetLayerSet().Seq()) == layers, f"Wrong keepout layers: {name}")
        require(all([zone.GetDoNotAllowTracks(), zone.GetDoNotAllowVias(),
                     zone.GetDoNotAllowPads(), zone.GetDoNotAllowZoneFills()]), f"Weakened keepout: {name}")
        polygon = zone.Outline().COutline(0)
        require([mm_pair(polygon.CPoint(i)) for i in range(polygon.PointCount())] == points,
                f"Changed keepout geometry: {name}")
    print(f"PASS: Two-layer 42 x 24 mm outline ({outline.Area() / 1e12:.2f} mm² material area), safety keepouts")
    # KiCad's text-thickness DRC does not cover thin footprint outline graphics.
    graphics = list(board.GetDrawings())
    for foot in feet.values():
        graphics.extend(foot.GraphicalItems())
    for item in graphics:
        if isinstance(item, k.PCB_SHAPE) and item.GetLayer() in (k.F_SilkS, k.B_SilkS):
            require(item.GetWidth() >= k.FromMM(.15), "Silkscreen graphic thinner than JLCPCB 0.15 mm profile")
    print("PASS: Silkscreen graphic strokes meet the 0.15 mm JLCPCB profile")
    print("Physical fit, RF, power, and monitor behavior remain untested.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
