# HDMI2C development plan

This is the handoff document for continuing work across sessions. Read it together
with `readme.md`, inspect the working tree, and update the checkboxes and session
notes after each meaningful change. Do not assume a checked design task has been
tested on physical hardware.

## Intended result

A small, inexpensive controller for one monitor, connected to a spare HDMI input
and controlled over Wi-Fi using ESPHome. Initial controls are brightness and input
selection through DDC/CI over I2C. The final MCU board is a Seeed Studio XIAO
ESP32-C6. USB supplies power; the HDMI connection does not carry video.

The stages below are sequential. The current implementation request is stage 1;
stages 2 and 3 are planned follow-ups.

## Stage 1 — one HDMI port

Keep the ESP32-WROOM-32 and HDMI1 (`J7`) to isolate this change from the MCU redesign.
Keep existing reference designators so diffs and earlier assembly information
remain easy to follow.

- [x] Inspect the schematic, PCB, libraries, README, and existing local changes.
- [x] Identify the complete HDMI2 circuit to remove:
  - connector `J8`;
  - shield and I2C jumpers `JP2`, `JP7`, `JP8`;
  - level shifters `Q4`, `Q6` and pull-ups `R8`, `R10`, `R12`, `R14`;
  - HPD divider `R20`, `R21`;
  - switchable 5 V supply `U5`, `Q8`, `C6`.
- [x] Capture baseline ERC/DRC results before editing.
- [x] Remove these symbols, their wires, labels, junctions, and cached instances.
  Mark the four freed MCU pins intentionally unconnected.
- [x] Remove matching footprints, HDMI2 nets, traces, and obsolete shared-supply
  branches from the PCB. Preserve the complete HDMI1 circuit.
- [x] Reduce the board outline, reposition affected mounting holes/artwork, and
  refill copper. Record the resulting dimensions and component-count reduction.
- [x] Verify schematic/PCB connectivity, ERC, DRC, and visual exports. Record
  inherited findings separately from regressions; resolve new electrical or
  mechanical errors introduced by this change.
- [x] Update README and record a stage-1 handoff here. Generated manufacturing
  files should only be treated as release files after the outstanding checks pass.

Acceptance: exactly one HDMI connector in schematic and PCB, no HDMI2 circuitry
or routing, HDMI1 pin connectivity preserved, a smaller board, and explicit
verification results. A physical build is a separate validation milestone.

## Stage 2 — XIAO ESP32-C6 carrier

- [ ] Read Seeed's schematic, pinout, dimensions, and CAD resources; record the
  exact module revision and resource versions used. The documented module size
  is 21 × 17.8 mm. This is a carrier redesign, not a pin-compatible WROOM swap.
- [ ] Add/verify a local symbol and footprint for the complete XIAO board,
  including pad numbering, mounting method, USB clearance, antenna clearance,
  and access to boot/reset. Prefer soldered castellated pads for compactness;
  check assembly access before fixing the layout.
- [ ] Create an explicit old-to-new signal mapping. Start with XIAO `D4/GPIO22`
  for SDA and `D5/GPIO23` for SCL; select remaining exposed GPIOs for HDMI 5 V
  enable, HPD input, and any retained buttons after checking boot constraints.
  Reserve the board's antenna-control GPIOs according to Seeed's documentation.
- [ ] Use the XIAO's USB-C power/programming connection and onboard regulation.
  Remove the redundant WROOM, USB connector, USB-UART bridge, auto-programming
  circuit, and associated parts once their replacement paths are confirmed.
- [ ] Review the HDMI electrical interface: 3.3 V/5 V level shifting, pull-ups,
  HPD divider, common ground/shield, ESD, enable defaults, and backfeed behavior.
  Audit the inherited 5 V LDO/pass-FET circuit with USB input voltage and dropout
  in mind before deciding to retain or replace it. Do not wire 5 V DDC directly
  to an ESP32 GPIO.
- [ ] Redraw and compact the carrier PCB around one HDMI connector and the XIAO.
  Revisit buttons and mounting holes only as needed for the smaller layout.
- [ ] Run ERC, DRC, schematic/PCB parity, and a physical footprint/connector
  review. Generate a BOM, assembly view, schematic PDF, Gerbers, and drills for
  the reviewed revision.
- [ ] Bring up hardware: check USB, 3.3 V and HDMI 5 V rails, boot/programming,
  Wi-Fi reception, DDC idle levels and waveforms, and HPD/enable behavior.

Acceptance: documented XIAO pin mapping, compact carrier, resolved release-blocking
CAD findings, successful power/programming/Wi-Fi bring-up, and an electrically
verified DDC connection. Record any checks that require a physical board.

## Stage 3 — ESPHome firmware over Wi-Fi

- [ ] Review the three reference projects below at recorded commits; inspect
  their actual DDC implementations and licenses before reusing code. MoniBee
  uses the ESP32-C6 with Zigbee and is a protocol reference, not the requested
  Wi-Fi/ESPHome implementation. Distinguish DDC/CI on HDMI SDA/SCL from CEC.
- [ ] Pin a supported ESPHome version and compile a minimal XIAO configuration
  using `variant: esp32c6` and the ESP-IDF framework. Confirm flash size, USB
  logging, antenna configuration, Wi-Fi, encrypted native API, and OTA. Keep
  credentials in an untracked `secrets.yaml` with a checked-in example.
- [ ] Implement a reusable local ESPHome external component for DDC/CI. Plan
  for a configurable I2C bus/address, checksums, response validation, explicit
  transaction timing, serialized requests, bounded retries, and offline recovery.
  Verify address notation (7-bit address versus shifted wire address) against
  the source implementations. Avoid an always-running I2C scan on the DDC bus.
- [ ] Add a brightness `number` entity and input-source `select` entity. Support
  monitor-specific source codes; confirm readback and brightness scaling against
  the monitor's reported range. Identify unsupported controls without blocking
  Wi-Fi/API operation. Add power control later if supported and useful.
- [ ] Add hardware pin substitutions, conservative polling, availability/error
  reporting, safe startup behavior, and optional button actions. Keep the bus
  state machine nonblocking so network and watchdog tasks continue to run.
- [ ] Verify framing/checksum/error handling with meaningful protocol tests and
  captured/known transactions; run ESPHome config validation and compilation.
- [ ] Test on a real monitor with DDC/CI enabled: brightness set/read, input
  switch/read, inactive spare HDMI input, cable reconnect, monitor sleep/wake,
  power loss, controller reboot, Wi-Fi loss/recovery, and OTA.
- [ ] Document flashing, ESPHome/Home Assistant setup, supported monitor models
  and settings, troubleshooting, and the exact tested hardware/firmware versions.

Acceptance: an ESPHome build for this board exposing working brightness and input
controls over Wi-Fi, with readback/error handling and recorded monitor tests.

## Constraints and decisions to carry forward

- Some monitors ignore DDC on inactive inputs. Test the actual target monitor
  early; firmware cannot guarantee support on an arbitrary spare HDMI port.
- Keep the monitor's normal video connection separate. HDMI passthrough, dual
  monitors on one carrier, Zigbee/Matter, and ambient-light/IR features are outside
  the current scope.
- Stage 1 keeps the existing power architecture and GPIO mapping. Stage 2 must
  review these instead of assuming the smaller board is electrically identical.
- Preserve user changes. At the start of this work, `hdmi2c.kicad_pro` already had
  KiCad version/settings changes, and `.history/` and `.idea/` were untracked.
- CAD formats retained: schematic 20211123 and PCB 20211014. KiCad CLI 10.0.6 is
  installed in the current environment. Zone refill was performed on a temporary
  copy and the filled polygon transferred back without converting the working
  board to the newer file format.

## References

Reviewed for planning on 2026-09-12; recheck versions before implementing firmware.

- [Seeed XIAO ESP32-C6 pinout and resources](https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/#resources)
  — module dimensions, GPIO mapping, power and antenna controls.
- [fluxfur/ddcBrightness](https://github.com/fluxfur/ddcBrightness)
  — existing HDMI monitor-control implementation to inspect for DDC behavior.
- [TeaRex-coder/hardwareddc firmware](https://github.com/TeaRex-coder/hardwareddc/tree/main/firmware)
  — ESP32 firmware; its [README](https://github.com/TeaRex-coder/hardwareddc)
  describes control through a spare HDMI input and links the DDC/VCP library.
- [ItsEcholot/MoniBee](https://github.com/ItsEcholot/MoniBee)
  — ESP32-C6 monitor control; inspect source rather than relying on its mixed
  CEC/DDC terminology. Its board is a C6 Supermini, not the XIAO.
- [ESPHome ESP32 platform](https://esphome.io/components/esp32/)
  — C6 variant and ESP-IDF support.
- [ESPHome external components](https://esphome.io/components/external_components/)
  — component integration approach to check during stage 3.

## Session handoff

### 2026-09-12 — plan and stage 1

Status: stage 1 complete in CAD; hardware validation remains outstanding.

- No firmware existed in this repository at the start of this work.
- Board outline reduced from 95 × 45 mm to 70 × 45 mm (26.3% less area). Removed
  15 circuit components; 46 PCB footprints remain including holes and artwork.
- HDMI1 (`J7`) is preserved, including its original GPIO26 SCL, GPIO27 SDA,
  GPIO16 HPD, and GPIO18 5 V enable mapping. Removed HDMI2 from both CAD files.
- Updated the local logo footprint and its PCB instance to fit the smaller board
  and identify it as `rev1`. The user-edited project settings were left intact.
- Verification: 88 matching pin groups, no unrouted connections, and no new ERC,
  DRC, or schematic/PCB parity findings compared with the baseline. Inherited
  findings remain (7 ERC errors and 10 DRC errors); this is not a fabrication
  release. See [stage-1 verification](docs/stage1-validation.md) for counts,
  retained pin mapping, limitations, and commands.
- Added `scripts/check_connectivity.py` for repeatable schematic/PCB pin-group
  comparison and optional comparison with an earlier netlist.
- Next implementation task: stage 2, starting with the official XIAO schematic,
  mechanical footprint, and explicit pin/power mapping. Review the inherited
  HDMI supply circuit and CAD findings as part of that redesign. Do not begin
  the ESPHome implementation with the old WROOM pin mapping.
