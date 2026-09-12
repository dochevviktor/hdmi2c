#!/usr/bin/env python3
"""Audit the nominal rev2 STEP assembly; does not qualify physical fit or RF.

Run after scripts/export_rev2.sh, using the optional requirements-3d.txt environment.
Checks XIAO-to-carrier/components, HDMI shell-to-FR4, and antenna projection.
It does not check solder, cable plugs, enclosure, tolerances, or internal XIAO parts.
"""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

from OCP.Bnd import Bnd_Box
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepGProp import BRepGProp
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.GProp import GProp_GProps
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS_Compound
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.collections import Sequence_TDF_Label
from OCP.gp import gp_Pnt

ROOT = Path(__file__).resolve().parents[1]
OTHER_PARTS = {"C1", "C2", "C3", "J7", "R24", "R25", "R26", "R27", "SW2", "SW3", "U4"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(shape):
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, box, False, False)
    low, high = box.CornerMin(), box.CornerMax()
    return [round(v, 6) for v in (low.X(), low.Y(), low.Z(), high.X(), high.Y(), high.Z())]


def compound(shapes):
    result, builder = TopoDS_Compound(), BRep_Builder()
    builder.MakeCompound(result)
    for shape in shapes:
        builder.Add(result, shape)
    return result


def read_leaves(path):
    """Resolve STEP/XCAF assembly instances into located leaf shapes."""
    doc = TDocStd_Document(TCollection_ExtendedString("rev2-audit"))
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    require(int(reader.ReadFile(str(path))) == 1, f"Cannot read STEP: {path}")
    require(reader.Transfer(doc), "Cannot transfer STEP assembly")
    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    roots = Sequence_TDF_Label()
    shape_tool.GetFreeShapes(roots)
    leaves = []

    def walk(label, location=TopLoc_Location(), names=()):
        name = TDataStd_Name()
        if label.FindAttribute(TDataStd_Name.GetID_s(), name):
            names = names + (name.Get().ToExtString(),)
        if shape_tool.IsReference_s(label):
            referred = TDF_Label()
            require(shape_tool.GetReferredShape_s(label, referred), "Broken STEP reference")
            walk(referred, location * shape_tool.GetLocation_s(label), names)
        elif shape_tool.IsAssembly_s(label):
            children = Sequence_TDF_Label()
            shape_tool.GetComponents_s(label, children, False)
            for i in range(1, children.Length() + 1):
                walk(children.Value(i), location, names)
        else:
            leaves.append((names, shape_tool.GetShape_s(label).Moved(location)))

    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i))
    return leaves


def separation(first, second):
    distance = BRepExtrema_DistShapeShape(first, second)
    require(distance.IsDone(), "Distance calculation failed")
    common = BRepAlgoAPI_Common(first, second)
    require(common.IsDone(), "Intersection calculation failed")
    properties = GProp_GProps()
    BRepGProp.VolumeProperties_s(common.Shape(), properties)
    volume = abs(properties.Mass())
    require(volume < 1e-6, f"Solid interference: {volume:.6f} mm³")
    return {"minimum_distance_mm": round(distance.Value(), 6),
            "intersection_volume_mm3": round(volume, 9)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    # Reject stale geometry before recording hashes of the current board alongside it.
    source_manifest = args.step.parent / "checks/source-sha256.txt"
    for line in source_manifest.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        require(sha256(ROOT / name) == digest, f"Stale export: {name}; rerun export_rev2.sh")
    require(args.step.stat().st_mtime >= (ROOT / "hdmi2c.kicad_pcb").stat().st_mtime,
            "STEP is older than the PCB; rerun export_rev2.sh")
    leaves = read_leaves(args.step)
    parts = {ref: compound([s for names, s in leaves if ref in names])
             for ref in OTHER_PARTS | {"U3"}}
    present = {ref for ref in parts if any(ref in names for names, _ in leaves)}
    require(present == set(parts), f"Missing component models: {set(parts) - present}")
    carrier_shapes = [s for names, s in leaves if names[-1] == "hdmi2c_PCB"]
    require(len(carrier_shapes) == 1, "Expected one carrier substrate")
    carrier = carrier_shapes[0]
    bodies = [s for names, s in leaves if "U3" in names and names[-1] == "COMPOUND"]
    antennas = [s for names, s in leaves if "U3" in names and "Ceramic Antenna" in names[-1]]
    usb = [s for names, s in leaves if "U3" in names and "USB TYPE C PORT" in names]
    require(len(bodies) == len(antennas) == 1 and usb, "Incomplete XIAO assembly")

    gaps = {ref: separation(parts["U3"], parts[ref]) for ref in sorted(OTHER_PARTS)}
    carrier_box, antenna_box = bounds(carrier), bounds(antennas[0])
    # Extrude the antenna's XY envelope through the substrate to test plan-view clearance.
    projection = BRepPrimAPI_MakeBox(
        gp_Pnt(antenna_box[0], antenna_box[1], carrier_box[2]),
        antenna_box[3] - antenna_box[0], antenna_box[4] - antenna_box[1],
        carrier_box[5] - carrier_box[2]).Shape()
    antenna_gap = separation(projection, carrier)
    require(antenna_gap["minimum_distance_mm"] > .001, "Antenna projection touches carrier")
    envelope = bounds(compound([carrier, *parts.values()]))
    closest = min(gaps, key=lambda ref: gaps[ref]["minimum_distance_mm"])
    report = {
        "status": "PASS (nominal CAD only)",
        "tool": "cadquery-ocp " + importlib.metadata.version("cadquery-ocp"),
        "source_manifest_sha256": sha256(source_manifest),
        "step_sha256": sha256(args.step),
        "pcb_sha256": sha256(ROOT / "hdmi2c.kicad_pcb"),
        "xiao_model_sha256": sha256(ROOT / "3d/Seeed_Studio_XIAO_ESP32C6.step"),
        "coordinates": "mm; X=PCB X, Y=-PCB Y, Z=KiCad STEP height; bounds=minXYZ,maxXYZ",
        "modeled_fitted_components": sorted(parts),
        "assembly_bounds": envelope,
        "assembly_size_mm": [round(envelope[i + 3] - envelope[i], 6) for i in range(3)],
        "xiao_board_bounds": bounds(bodies[0]),
        "xiao_usb_bounds": bounds(compound(usb)),
        "xiao_antenna_bounds": antenna_box,
        "xiao_to_components": gaps,
        "closest_component_to_xiao": closest,
        "xiao_to_carrier_substrate": separation(parts["U3"], carrier),
        "hdmi_to_carrier_substrate": separation(parts["J7"], carrier),
        "antenna_projection_to_carrier": antenna_gap,
        "limitations": [
            "Older 2024 XIAO model; actual purchased module revision must be checked.",
            "No solder, cables/plugs, enclosure, manufacturing tolerances, or load analysis.",
            "Substrate separation excludes copper/mask; it is not a specified solder standoff.",
            "Antenna clearance is geometric only, not an RF keepout recommendation or RF test.",
            "Checks only the listed external pairs, not internal XIAO component intersections.",
            "STEP/source hashes must match the reviewed files; rerun after re-exporting.",
        ],
    }
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
        print(f"PASS: nominal 3D clearances; nearest to XIAO is {closest} "
              f"at {gaps[closest]['minimum_distance_mm']:.2f} mm; report: {args.output}")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
