# Stage 2 — XIAO ESP32-C6 carrier (rev2)

Design date: 2026-09-12. This is a prototype design, not tested hardware.
See [PLAN.md](../PLAN.md) for project status and the remaining bring-up work.
The ESPHome implementation is still stage 3; no working firmware is implied.

## What changed

The complete Seeed Studio XIAO ESP32-C6 replaces the bare WROOM module. Its
USB-C socket, native USB programming, regulator, RF circuit, and boot/reset
buttons replace the carrier's USB socket, CP2102N, regulator, programming
transistors, and reset circuit. There is no battery connection on this carrier.

The single HDMI connector remains `J7`, Würth **685119134923**. The old discrete
DDC level shifters, HPD divider, jumpers, and HDMI supply circuit are replaced by
`U4`, **TPD12S016PWR**, in the solderable **PW/TSSOP-24** package. This is not the
pin-compatible UQFN version. The old nominal 5 V LDO is no longer in the USB-to-HDMI
path, avoiding its input-headroom problem. Component references reused across
revisions do not imply interchangeable parts; use the rev2 BOM and schematic.

The carrier has a **42 × 24 mm bounding box**, versus 70 × 45 mm in stage 1:
68% less bounding-box area. The antenna notch removes additional material.
There are **12 fitted components**, plus four etched test pads (16 footprints).
The XIAO counts as one purchased assembly; its onboard parts are not counted
individually. Mounting holes are omitted. Two smaller, top-actuated
Omron B3U-1000P buttons replace the original forward-facing switches.

## Pin and power contract for firmware

The table uses **physical XIAO castellation numbers**, not ESP32 chip pad numbers.
KiCad's local net names acquire a leading `/` in the netlist.

| Function / net | Old WROOM GPIO | XIAO label | ESP32-C6 GPIO | U3 pad | Other endpoint |
| --- | --- | --- | --- | --- | --- |
| `I2C_SDA` | 27 | D4 | 22 | 5 | U4.3 SDA_A |
| `I2C_SCL` | 26 | D5 | 23 | 6 | U4.2 SCL_A |
| `HDMI_5V_EN`, active high | 18 | D0 | 0 | 1 | U4.12 CT_HPD |
| `DDC_EN`, active high | New | D1 | 1 | 2 | U4.5 LS_OE |
| `HDMI_HPD`, input | 16 | D2 | 2 | 3 | U4.4 HPD_A |
| `BUTTON1`, active low | 13 | D8 | 19 | 9 | SW2.1 |
| `BUTTON2`, active low | 14 | D9 | 20 | 10 | SW3.1 |
| `+3V3`, regulator output | — | 3V3 | — | 12 | U4.24 VCCA; button pull-ups |
| `GND` | — | GND | — | 13 | Common carrier/HDMI ground |
| `VBUS`, USB 5 V | — | 5V | — | 14 | U4.11 VCC5V |

Unused castellations 4, 7, 8, and 11 are intentionally unconnected. No carrier
signal uses the C6 strapping GPIOs 4, 5, 8, 9, or 15, or its native USB GPIO12/13.
The module retains its own boot/reset buttons. Mapping was checked against Seeed's
schematic/pinout and the [Espressif datasheet, v1.5](https://www.espressif.com/sites/default/files/documentation/esp32-c6_datasheet_en.pdf).

Reserve internal **GPIO3** for RF-switch enable (low) and **GPIO14** for antenna
selection (low for onboard ceramic, high for external). These are not carrier
I/O. Stage 3 must initialize them using the selected framework's XIAO support or
explicit startup configuration. See [Seeed's RF-switch instructions](https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/#hardware-overview).

Suggested startup sequence for stage 3:

1. Set `HDMI_5V_EN` and `DDC_EN` low before configuring monitor control.
2. Initialize the XIAO antenna selection and Wi-Fi; configure HPD as an input.
3. Assert `HDMI_5V_EN`, then allow a conservative 10 ms initial settling interval.
   This is a proposed firmware margin, not a measured monitor-ready time.
4. Assert `DDC_EN`; start DDC at 100 kHz with open-drain signaling and bounded
   timeouts. Verify clock stretching, signal levels, and transaction timing on
   hardware before relying on communication.
5. To turn the HDMI interface off, disable DDC first, then remove HDMI 5 V.

Never intentionally leave LS_OE high with CT_HPD low: TI marks that state invalid.
HPD is advisory for this application; do not assume an inactive monitor input
must report HPD before trying DDC. Monitor readiness and retry timing need actual
monitor tests. The new `DDC_EN` output is mandatory, not interchangeable with the
old single-enable firmware wiring. R24/R25 are 100 kΩ pulldowns; R26/R27 are
10 kΩ button pull-ups. Both buttons short their signals to ground when pressed.

## HDMI electrical interface

| J7 pin | Signal | U4 PW pin / connection |
| --- | --- | --- |
| 15 | SCL, 5 V side | 8 SCL_B |
| 16 | SDA, 5 V side | 9 SDA_B |
| 17 | DDC ground | Common GND |
| 18 | Switched HDMI 5 V | 13 5V_OUT |
| 19 | HPD, 5 V side | 10 HPD_B |
| 2, 5, 8, 11, SH | Pair shields / shell | Common GND |

U4 ground pins **6, 14, and 19** all connect to ground. Unused CEC pins 1/7 and
TMDS clamp pins 15/16/17/18/20/21/22/23 are intentionally unconnected; this board
does not send video. C1/C2/C3 are 100 nF bypass capacitors on VCC5V, VCCA, and
5V_OUT respectively, with short local connections and nearby ground vias.

The [TI datasheet, SLLSE96F, October 2015](https://www.ti.com/lit/ds/symlink/tpd12s016.pdf)
specifies integrated DDC pull-ups (10 kΩ to VCCA; 1.75 kΩ to 5V_OUT), level
translation, HPD buffering, and connector-side protection. Do not fit extra DDC
pull-ups by default. The HDMI supply supports a 55 mA load; short-circuit limiting
is 150 mA typical (100–200 mA), **not a precise 55 mA cutoff**. Output drop is
50 mV maximum at 55 mA under the stated test conditions. Reverse-current blocking
is specified on 5V_OUT and the cable-side DDC/CEC pins when powered down. These
component specifications do not establish board-level ESD or HDMI certification.

USB supplies both the XIAO and HDMI load. Do not inject a second supply into
U3.14/TP1 or connect a battery for this revision. Test cable/supply voltage drop
and Wi-Fi transients. The buffered DDC interface has an A-side low-level offset;
bench-check logic-low margins and avoid cascading another offset-type bus buffer
without an electrical review. Keep the HDMI cable disconnected for initial
power-up and solder inspection.

## Mechanical and assembly review

- Two copper layers, nominal 1.6 mm FR-4. The board outline has 1 mm radii and an
  open antenna notch. Copper clearance to the outline is 0.3 mm minimum.
- U3 is soldered by its 14 side castellations, with USB at the carrier's upper
  edge. Its PCB body is nominally 21 × 17.8 mm. The USB socket projects beyond the
  carrier outline; 42 × 24 mm describes the carrier, **not the assembled envelope**.
- The local XIAO footprint preserves Seeed's side-pad coordinates, size, and
  numbering. Underside debug/test/battery lands 15–24 were deliberately removed.
  The interior beneath the module prohibits front copper, pads, and vias so
  exposed underside module contacts cannot touch carrier conductors.
- The antenna is over the notch at the opposite end from USB. A separate rule
  area prohibits copper, traces, vias, and pads on **both copper layers**. Keep
  an enclosure, metal fasteners, and cables away from this end; RF performance
  and enclosure clearance are not validated by DRC.
- The XIAO top-side boot/reset buttons and external antenna socket remain
  accessible. Side solder fillets remain reachable. Assemble the low components
  first, inspect for bridges, then fit the module/HDMI socket as appropriate to
  the assembly process. Verify a 1:1 print against actual parts before ordering.
- J7 faces the right edge. Its original SMT and plated-slot land geometry is
  retained, reviewed against the [Würth drawing, rev. 001.002](https://www.we-online.com/components/products/datasheet/685119134923.pdf).
  The body/courtyard and local STEP transform are included. Through-hole shell
  tabs require solder; an SMT-only assembly operation is insufficient.
- There are no screw holes. Provide nonconductive enclosure support and cable
  strain relief; do not treat the castellated joints as cable-load supports.
- All fitted parts are on the front. TP1–TP4 are **back-side** exposed pads:
  HDMI 5 V, GND, SCL, SDA. Back assembly plots are mirrored for a bottom view.
- Seeed's linked GrabCAD model returned HTTP 403 during this session. No detailed
  XIAO STEP model is included or claimed as checked. Module positioning uses the
  official 2D CAD; exact assembled height and enclosure fit still need a model or
  physical sample. Do not infer complete assembly clearance from a partial 3D view.

## Resource provenance

Resources were retrieved on 2026-09-12 from the [Seeed resource list](https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/#resources).

| Resource | Version / use |
| --- | --- |
| [XIAO schematic PDF](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32C6/XIAO_ESP32_C6_v1.0_SCH_260114.pdf) | V1.0, title dated 2026-01-14; power, pinout, RF, controls |
| [XIAO KiCad project](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32C6/XIAO_ESP32_C6_v1.0_SCH&PCB_260114.zip) | Archive named 260114; PCB entry dated 2025-02-11, schematic entries January 2026; layout/mechanics cross-check |
| [XIAO footprints](https://files.seeedstudio.com/wiki/XIAO-KiCad-Library/New_XIAO_Series_Footprints.zip) | `XIAO-ESP32-C6-SMD.kicad_mod`, entry dated 2026-01-05; adapted as `hdmi2c:XIAO_ESP32C6_Castellated` |
| [XIAO symbols](https://files.seeedstudio.com/wiki/XIAO-KiCad-Library/XIAO_Series_SCH_Symbols.zip) | Used as a pinout reference; local symbol describes the 14 connected castellations and power direction |
| [Pinout workbook](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32C6/res/XIAO_ESP32C6_Pinout.xlsx) | Cross-check of GPIO labels |
| [XIAO 3D model](https://grabcad.com/library/seeed-studio-xiao-esp32-c6-1) | Inaccessible (HTTP 403); outstanding detailed mechanical reference |
| [Omron B3U datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf) | B3U-1000P, non-illuminated top-actuated switch |

Downloaded Seeed source hashes (SHA-256):

```text
510f3f917bcded1201ca5c63374409183457c1ef83a836988517d6802180dad7  schematic PDF
cea2ed66da575e4a1dd6c7a9acd60583ed4a9adbf6b1d2952851c1e4199c05fc  KiCad project ZIP
36f7e87db783002f20dad0fb36136c877dbc49e051293997993a988cac065698  footprint ZIP
9a423cc0683f3f6a2716a47f817556bfe0bc1a9720041712cad36902a0c25fe5  symbol ZIP
e2dae530c359e66ba704039f86cfea4bc316596fde367d992723509777746494  pinout XLSX
```

Attribution: XIAO design and source library by Seeed Studio; the source schematic
credits Linus.Liao and carries CC BY-SA 4.0. The adapted XIAO footprint preserves
that attribution and is provided under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Adaptations are limited to the carrier mounting lands, fabrication graphics,
courtyard, name, and description. This notice does not relicense unrelated
original HDMI2C assets or third-party KiCad libraries.

## Physical bring-up — not performed

- [ ] Inspect part orientation, castellations, TSSOP solder bridges, and HDMI slots.
- [ ] Verify unpowered resistance between each supply rail and ground.
- [ ] With HDMI disconnected, power from a current-limited USB supply and check
  VBUS/3V3, reset-off enables, temperature, and absence of unexpected HDMI 5 V.
- [ ] Verify USB enumeration, native flashing/logging, boot/reset, and both buttons.
- [ ] Exercise enables; check HDMI 5 V under load and disabled/powered-off backfeed
  behavior with controlled equipment, without using a monitor as a fault fixture.
- [ ] Verify Wi-Fi reception with the intended antenna, USB/HDMI cables, enclosure,
  and worst-case transmit activity; check supply dips and resets.
- [ ] Check DDC idle/low levels, rise times, clock stretching, HPD, and enable order.
- [ ] Test a monitor's active and inactive HDMI inputs, sleep/wake and cable reconnect.
- [ ] Complete stage-3 firmware tests before claiming brightness/input control works.

## CAD verification and handoff

Checked with **KiCad CLI / pcbnew 10.0.6** on 2026-09-12. The schematic was redrawn
in format 20250114; the new PCB uses format 20260206. Use KiCad 10 for this revision.
This intentionally supersedes stage 1's legacy-format preservation. Existing
unrelated project preferences were preserved; minimum clearance, copper-to-edge,
and silkscreen spacing are now 0.20, 0.30, and 0.10 mm respectively. There are no
DRC exclusions. Stage 1's 7 ERC and 10 DRC errors no longer apply to this redesign.
Results use the project's configured severities. Six inherited checks remain
ignored (missing courtyard, track endpoint centered on via, tuning-profile
geometry, footprint filters, and PTH/NPTH inside courtyard); the JSON report
lists them explicitly. No rules were disabled to obtain the rev2 result.

| Check | Result |
| --- | --- |
| ERC, including warnings | 0 findings |
| DRC, all-track errors, including warnings | 0 findings |
| Unrouted connections | 0 |
| KiCad schematic/PCB parity | 0 findings |
| Independent electrical-contract / netlist comparison | 38 matching pin groups, including 24 intentional NC groups |
| XIAO footprint comparison to downloaded Seeed library | All 14 side-pad positions, sizes, and numbers match |
| PCB outline | 42 × 24 mm; approximately 915.64 mm² material area |
| Regression tests | 6 pass: valid design and five deliberate fault cases |
| Visual review | Schematic, front/back assembly and copper, plated-slot drill output |
| Physical, RF, USB/programming, monitor, and ESD tests | Not performed |

The routing was assisted locally by Freerouting 2.4.1, with manual local bypass
connections and ground-return vias, followed by KiCad clearance corrections and
zone refill. KiCad DRC is the final CAD acceptance check, not the router's score.
There are 221 track segments and 33 vias. No fabrication order was placed.

The [prototype package](../hardware/rev2/README.md) contains the BOM, placements,
assembly drawings, schematic PDF, Gerbers, drills, and machine-readable reports.
Run `bash scripts/export_rev2.sh` after edits; it stops on failed checks.
`python3 -m unittest discover -s tests -v` exercises swapped SDA/SCL, a direct
5 V-to-GPIO miswire, changed land geometry, and missing/weakened antenna keepouts.
These are design-regression checks, not circuit simulation or evidence that DDC
works on a monitor.

Next: use the 1:1 fit print and physical bring-up checklist before trusting a
prototype. Stage 3 can begin its ESPHome component/configuration work against the
pin contract above when requested, without marking the physical stage-2 milestone
complete. Obtain the XIAO model or measure a sample before enclosure design.
