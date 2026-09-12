# Local 3D models

## XIAO ESP32-C6

`Seeed_Studio_XIAO_ESP32C6.step` is the unmodified STEP supplied by the user in
`seeed-studio-xiao-esp32-c6-1.snapshot.3.zip` on 2026-09-12. It comes from the
[GrabCAD entry](https://grabcad.com/library/seeed-studio-xiao-esp32-c6-1) linked by
[Seeed's resource page](https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/#resources).
The earlier HTTP 403 download limitation is resolved by this local snapshot.

- Original filename: `Seeed Studio XIAO ESP32-C6.step`.
- STEP header timestamp: 2024-11-06T17:15:41+01:00; archive entries: 2024-11-07.
- STEP AP214, millimetres; header identifies Autodesk Translation Framework.
- Assembly label: `Seeed Studio XIAO ESP32-C6 v7`. This is a **CAD model label**,
  not evidence of a hardware V7 revision. It predates the 2026 V1.0 schematic
  used for the carrier's electrical design. Verify the actual purchased module.

SHA-256:

```text
d4d2e3a05c969d69077b256c8b1567805f29be1901635768448c9dc12687c388  supplied ZIP
2e1ce01f4497192485823ca9fffd68e323bafc84cd7b85c2906b5497550be8fc  imported STEP
```

The archive includes front/back reference images but no explicit license or
author attribution file. Retain the source link and verify the applicable terms
before externally redistributing this model or derived assembly exports. The
Seeed schematic/footprint CC BY-SA notice does **not** establish this model's
license. No external publication was performed as part of this integration.

## XIAO placement in KiCad

The library footprint and U3 PCB instance both use
`${KIPRJMOD}/3d/Seeed_Studio_XIAO_ESP32C6.step`, with:

| Setting | X | Y | Z |
| --- | ---: | ---: | ---: |
| Offset, mm | 15.0014 | 8.759341 | 0.25 |
| Scale | 1 | 1 | 1 |
| Rotation, degrees | -90 | 0 | -90 |

The source axes map to footprint 3D axes as `(X,Y,Z) = (source Z, source X,
source Y)` before translation. The source board underside is at Y = -0.25 mm;
the Z offset places it at the mounting plane. It is **not a 0.25 mm standoff**.
The source body is 17.780 × 20.955 × 1.250 mm, close to the official nominal
17.8 × 21 mm outline; it is not scaled to hide this difference. All seven
castellation row centres on both sides align with the carrier's 2.54 mm pitch.
The USB points outward and the ceramic antenna lies over the open notch.

See the [mechanical review](../docs/stage2-hardware.md#detailed-3d-review) and
[rev2 assembly exports](../hardware/rev2/README.md) for clearances, limitations,
and repeatable commands. Other models in this folder predate this integration;
their existing provenance and rights are unchanged.
