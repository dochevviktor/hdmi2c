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

The stages below are sequential. Stage 1 is complete in CAD. The current
implementation request is stage 2; stage 3 is the planned firmware follow-up.
Stage 2 is now complete in CAD as `rev2`; its physical bring-up is still pending.

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

- [x] Read Seeed's schematic, pinout, dimensions, and CAD resources; record the
  exact module revision and resource versions used. The documented module size
  is 21 × 17.8 mm. This is a carrier redesign, not a pin-compatible WROOM swap.
- [x] Add/verify a local symbol and footprint for the complete XIAO board,
  including pad numbering, mounting method, USB clearance, antenna clearance,
  and access to boot/reset. Prefer soldered castellated pads for compactness;
  check assembly access before fixing the layout.
- [x] Create an explicit old-to-new signal mapping. Start with XIAO `D4/GPIO22`
  for SDA and `D5/GPIO23` for SCL; select remaining exposed GPIOs for HDMI 5 V
  enable, HPD input, and any retained buttons after checking boot constraints.
  Reserve the board's antenna-control GPIOs according to Seeed's documentation.
- [x] Use the XIAO's USB-C power/programming connection and onboard regulation.
  Remove the redundant WROOM, USB connector, USB-UART bridge, auto-programming
  circuit, and associated parts once their replacement paths are confirmed.
- [x] Review the HDMI electrical interface: 3.3 V/5 V level shifting, pull-ups,
  HPD divider, common ground/shield, ESD, enable defaults, and backfeed behavior.
  Audit the inherited 5 V LDO/pass-FET circuit with USB input voltage and dropout
  in mind before deciding to retain or replace it. Do not wire 5 V DDC directly
  to an ESP32 GPIO.
- [x] Redraw and compact the carrier PCB around one HDMI connector and the XIAO.
  Revisit buttons and mounting holes only as needed for the smaller layout.
- [x] Run ERC, DRC, schematic/PCB parity, and a datasheet/2D footprint/connector
  review. Generate a BOM, assembly view, schematic PDF, Gerbers, and drills for
  the reviewed revision.
- [x] Integrate the user-supplied detailed XIAO STEP model; align it in the library
  and PCB, review nominal solid clearances, and export assembly STEP/front/back
  views. Record model provenance, transform, and repeatable checks.
- [ ] Verify the 1:1 land print against physical samples and assembled/enclosure
  clearances. Compare the 2024 model snapshot with the actual purchased module;
  cable plugs, solder, tolerances, and RF behavior remain unverified.
- [x] Review the supplied JLCPCB template and matching BOM; apply appropriate
  KiCad 10 factory limits, update silk, preserve the raw matching CSV, and save
  reviewed purchasing fields with a guarded draft export.
- [x] Update the review workflow for KiCad 10, share local/CI validation, retain
  the interactive BOM preview, and prevent pull-request Pages deployments.
  Verify the build locally in its pinned container; no remote run/publication.
- [x] Confirm J7's exact catalog identity: Würth 685119134923 / C2930961; update
  purchasing fields/BOM without a footprint substitution. All 12 identities match.
- [ ] Complete JLCPCB assembly preparation: confirm current availability, complete
  XIAO reflow/handling and HDMI shell-tab soldering, choose service/tooling/panel
  needs, and verify the final CPL offsets/rotations and placement preview.
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
- Stage 1 kept the existing power architecture and GPIO mapping. Stage 2 replaces
  these with the XIAO and TPD12S016PWR; use the new firmware pin contract in
  [stage-2 hardware notes](docs/stage2-hardware.md), including the new DDC enable.
- Preserve user changes. At the start of this work, `hdmi2c.kicad_pro` already had
  KiCad version/settings changes, and `.history/` and `.idea/` were untracked.
- Stage 1 retained schematic 20211123 / PCB 20211014. The stage-2 redraw uses
  schematic 20250114 / PCB 20260206, verified with KiCad 10.0.6. Use KiCad 10 for
  the new carrier. The rev1 files remain available in Git history.

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

### 2026-09-12 — stage 2 XIAO carrier

Status: **CAD complete; physical stage-2 acceptance not yet achieved.** Stage 3
firmware remains unimplemented. Baseline at this session's start: `af1aed1`.

- U3 is the complete XIAO ESP32-C6 V1.0, using Seeed's January 2026 schematic and
  reviewed 14 castellation lands. Resource links, hashes, and attribution are in
  [stage-2 hardware notes](docs/stage2-hardware.md).
- Replaced the WROOM support circuits and discrete HDMI interface with a
  USB-powered XIAO plus TPD12S016PWR. DDC remains properly level translated;
  CT_HPD and LS_OE have independent GPIOs and reset-off pulldowns. HDMI shell and
  signal grounds are now directly common. No external battery supply is used.
- Board is 42 × 24 mm (68% smaller bounding-box area than stage 1), with antenna
  cutout and copper keepouts. 12 fitted components / 16 footprints, including
  two smaller top-actuated buttons and four back-side test pads. No screw holes.
- Pin contract: GPIO22 SDA, GPIO23 SCL, GPIO0 HDMI 5 V enable, GPIO1 DDC enable,
  GPIO2 HPD, GPIO19/20 buttons. Reserve GPIO3/14 for the XIAO antenna controls.
  Enable HDMI 5 V before DDC; disable DDC before removing HDMI 5 V.
- Verification: 0 ERC, 0 DRC, 0 unrouted, 0 parity findings; 38 matching pin
  groups; all 14 lands compared against Seeed; six regression tests pass.
  No exclusions were introduced. All CAD issues inherited from rev1 are gone.
- Generated [rev2 prototype package](hardware/rev2/README.md), including BOM,
  assembly views, 1:1 fit print, schematic PDF, Gerbers, drills, and reports.
  Reproduce with `bash scripts/export_rev2.sh`; it gates exports on checks/tests.
- Unrelated user changes in `.history` were preserved. Existing upstream Pages
  automation was not upgraded or run. No order, push, or commit was made.
- Next physical action: verify actual parts against the fit print, then perform
  the power/USB/RF/DDC bring-up checklist. Detailed XIAO 3D fit remains pending.
  Next software action, when requested: start stage 3 against the rev2 pin contract,
  review reference project commits/licenses, then pin and compile ESPHome/C6.

### 2026-09-12 — detailed XIAO 3D model follow-up

Status: **nominal 3D review complete; physical stage-2 acceptance still pending.**
Baseline: `59bcef6`. The user supplied the previously inaccessible GrabCAD ZIP.

- Imported its STEP unchanged as `3d/Seeed_Studio_XIAO_ESP32C6.step` and linked it
  with the same transform in the local footprint and U3 PCB instance. Source
  dates, hashes, coordinate alignment, and licensing caveat are in
  [3d/README.md](3d/README.md). It is a 2024 model, not confirmation of the exact
  2026 schematic/purchased board revision; its `v7` label is not a hardware revision.
- All 14 castellation rows align. No nominal solid interference between the
  XIAO and carrier/other fitted parts; nearest component R24 is 1.82 mm away.
  HDMI shell tabs also clear the carrier substrate through their slots.
- Antenna projection is over the notch, with approximately 0.294 mm minimum
  planar distance to carrier material. This small margin is geometric only;
  physical Wi-Fi/enclosure/cable testing remains mandatory, not a CAD pass.
- Assembly model envelope is approximately 43.90 × 25.51 × 8.38 mm, including
  connector overhangs and shell tabs, excluding solder/cables. Added front/back
  renders, assembly STEP, and a hashed [solid-check report](hardware/rev2/checks/mechanical-3d.json).
- No schematic, land geometry, routing, board-outline, or BOM changes. U3 still
  counts as one purchased assembly; there are 12 fitted components.
- Verification: 0 ERC/DRC/parity/unrouted findings, 38 matching pin groups, and
  nine regression tests pass, including missing/rotated/misplaced model cases.
  `scripts/export_rev2.sh` now exports the 3D assets and hashes the local models.
  A separate optional OpenCascade audit refreshes the solid-check report; see
  [package instructions](hardware/rev2/README.md#repeat-the-solid-clearance-review).
- Unrelated `.history` changes were preserved. No commit, push, publication,
  fabrication order, physical test, or stage-3 firmware implementation was done.
- Next physical action: compare an actual XIAO/HDMI socket with the 1:1 print and
  model, check mating plugs/enclosure support, then run the power/USB/RF/DDC
  checklist. Next software action, when requested: stage 3 against the rev2 pins.

### 2026-09-12 — JLCPCB template and BOM preparation

Status: **CAD profile checked; JLCPCB assembly release blocked by sourcing and
placement/assembler approval.** Baseline `26b2222`; the user's `bom.csv` and
unrelated `.history` changes were already present and were preserved.

- Extracted the supplied template ZIP and inspected `JLCPCB_1-2Layer`. It is a
  2019 KiCad 5 snapshot that unexpectedly enables four copper layers. Kept the
  actual two-layer, 1.6 mm carrier and existing 0.20 mm track/clearance rules.
  Compared relevant limits with JLCPCB's current primary documentation. Applied
  the conservative 1 oz/green-mask profile in [JLCPCB notes](docs/jlcpcb.md).
- Strengthened via/ring/hole, mask and silk settings; enlarged/repositioned silk
  text and increased 33 silk graphics to 0.15 mm. No pad, route, via, footprint
  placement, board outline, or electrical-connectivity changes.
- Saved the six suitable user-selected MPN/LCSC groups (11 fitted parts) in the
  schematic and PCB. **J7's C516617 / PI3HDMI1310-AZLEX match is an IC, not the
  Würth 685119134923 connector.** It was not adopted. The existing connector is
  retained pending the user's sourcing/replacement choice.
- `bom.csv` stays byte-identical to the user's matching export. Regeneration now
  writes `bom-design.csv` and `bom-jlcpcb-draft.csv`; J7 stays in the draft with
  its correct MPN and blank LCSC code. The purchasing report remains blocked,
  and strict checking exits nonzero. Duplicate headers, ranged references, and
  multiline CSV fields are handled without silently choosing the wrong column.
- Verification: 0 ERC/DRC/parity/unrouted findings; 38 matching pin groups;
  16 regression tests pass (10 design, 6 BOM). Nominal 3D clearances unchanged;
  refreshed prototype outputs and source hashes. The solid-check report was
  still stale at this handoff and was corrected on 2026-09-13 below. No rule
  severity reductions, DRC exclusions, order, upload, reservation, commit, or push.
- Next action: resolve whether to source/consign the Würth connector, hand-fit it,
  or investigate a JLCPCB-stocked replacement (requires footprint review before
  adoption). Confirm XIAO reflow/handling, mixed SMT/slot soldering, service and
  tooling with JLCPCB. Economic's published size minimum accommodates 42 × 24 mm;
  Standard would require a panel/tooling solution. This is not an assembler approval.
- `positions-front.csv` remains raw KiCad data: custom U3/J7 origins need CPL
  offset/rotation verification and a placement-preview review before ordering.
  Physical fit/RF/power/DDC tests and stage-3 firmware remain unperformed.

### 2026-09-13 — JLCPCB verification and review workflow

Status: **CAD/preview checks pass; assembly sourcing and physical acceptance remain
pending.** Baseline `f5ea02e` contains the preceding JLCPCB preparation. Only the
unrelated `.history` changes were present at this session's start and were preserved.

- Confirmed all current source hashes and the byte-identical user `bom.csv`.
  The nominal solid report still referenced the pre-JLCPCB export; reran the
  pinned OpenCascade audit against the current STEP. All clearances are unchanged
  and the report now records the current STEP/PCB/manifest hashes. No CAD geometry,
  component choices or routing changes were made in this session.
- Replaced the attached workflow's KiCad 6 generator and obsolete Actions with
  the official KiCad 10.0.5 container and InteractiveHtmlBom 2.12.0. Dependencies
  are pinned by digest/commit. The official 10.0.6 image was not yet available.
  Both the local 10.0.6 build and exact 10.0.5 container build pass.
- Added a shared `validate_rev2.sh` gate used by the full prototype exporter and
  the new 2D review-site builder. It preserves the user matching CSV and permits
  only the known J7 exception for a draft. The site excludes the raw CSV, full
  fabrication package, placements and 3D assets; it labels the J7/assembly blockers.
- Pull requests produce review artifacts only; only `main` can upload/deploy
  Pages. Checkout credentials are not persisted, build permissions are read-only,
  and deploy permissions are isolated. Existing output directories are rejected
  to avoid overwriting user files or publishing stale assets.
- Verification: 0 ERC/DRC/parity/unrouted findings, 38 matching pin groups, and
  **18 passing tests** (10 design, 6 purchasing, 2 preview safety), including in
  the pinned container with a read-only project mount and no network. Inspected
  the interactive BOM in Firefox: 7 groups / 12 parts, correct J7 socket MPN with
  blank LCSC code, four test pads excluded. Index links, actionlint, ShellCheck,
  shell syntax and whitespace checks pass. Strict BOM checking still exits 1.
- Reproduction, dependencies and CI limitations are in [automation notes](docs/automation.md).
  No commit, push, GitHub run, artifact upload, Pages deployment, reservation,
  fabrication order, physical test or firmware implementation was performed.
- Next action still requires the J7 sourcing decision: retain the Würth socket
  for sourcing/consignment/hand-fitting, or authorize investigation of a stocked
  replacement and its footprint. Final CPL/assembler approval and physical tests
  remain outstanding. The owner can review/commit/push the workflow and verify
  GitHub Pages configuration separately; a green review is not assembly approval.

### 2026-09-13 — exact J7 catalog match and submission checklist

Status: **all 12 fitted part identities matched; final CPL and assembly-process
approval remain pending.** Baseline `9723b97`; unrelated `.history` changes preserved.

- The user supplied C2930961. Verified JLCPCB and LCSC identify it as the exact
  Würth 685119134923 already used by J7. Rechecked the manufacturer's land pattern:
  19 signal lands, 0.50 mm pitch, 0.28 × 2.60 mm pads and 14.50 mm shell-column
  spacing. Added only the hidden LCSC field in schematic/PCB; no footprint, slot,
  routing, outline, model or pin-mapping change.
- Corrected only J7's matching-CSV row on that selection. Cleared the old IC's
  pricing, stock/MOQ and account quantities; retained the user's quantity five.
  All other rows remain byte-identical. The original row is recoverable in Git
  history; export scripts still never overwrite the matching input. New CSV SHA-256:
  `41d7cd4179fb72cbd5afe507a82e5c78174dc66418836862444c5367fa45a1ee`.
- Updated the reviewed purchasing contract and removed the J7 export exception.
  Strict checking accepts all 12 current identities and still rejects the saved
  old IC snapshot. Added tests for accepting C2930961 and rejecting that code
  with a different footprint. The clean draft BOM now has seven fully matched
  groups; `ready_for_order` remains false because placement/process checks are separate.
- Regenerated the prototype package, source hashes and nominal 3D audit. All
  solid clearances remain unchanged. Full export and native/pinned-container
  preview builds pass: 0 ERC/DRC/parity/unrouted findings, 38 matching pin groups,
  and **20 tests** (10 design, 8 purchasing, 2 preview safety). No check exclusions.
- Updated README, package notes and the review site to distinguish matched parts
  from assembly approval. Recorded the normal three-file-set handoff in
  [JLCPCB submission notes](docs/jlcpcb.md#files-to-submit): fabrication ZIP
  including drills/outline, clean BOM, and finalized centroid/CPL from one revision.
- Next action: prepare/review the final JLCPCB CPL (column names plus U3/J7
  offsets/rotations), inspect the placement preview, and confirm complete-XIAO
  reflow/handling, four HDMI shell-tab solder joints, service/tooling and stock.
  `positions-front.csv` is still raw KiCad data, not an approved CPL. Physical
  bring-up and firmware remain separate pending stages. No order, upload,
  reservation, commit, push, GitHub deployment or physical test was performed.

### 2026-09-13 — JLCPCB draft CPL

Status: **JLCPCB-format draft CPL generated; U3/J7 centroid corrections, rotation
review and assembler approval remain pending.** Baseline `8b7c0f0` plus the user's
uncommitted CPL exporter, its tests and `export_rev2.sh` hook; `.history` preserved.

- Reviewed `scripts/export_jlcpcb_cpl.py` and `tests/test_jlcpcb_cpl.py` without
  changing them. The header, column order and `mm` values match JLCPCB's sample
  CPL; `Top`/`Bottom` is an accepted layer form and rotations stay counter-clockwise.
- Generated `hardware/rev2/cpl-jlcpcb-draft.csv` and `checks/jlcpcb-cpl.json` from
  the placement file and draft BOM, which match fresh KiCad 10.0.6 regenerations.
  All 12 designators match the BOM; XY and rotations are copied unchanged.
- JLCPCB defines Mid X/Mid Y as centroids. pcbnew shows only U3 and J7 differ from
  their pad centres (+8.917/+10.500 mm and +3.450/0 mm), so the unmodified draft
  would misplace them. Details are in the [JLCPCB notes](docs/jlcpcb.md).
- Verification: `validate_rev2.sh` passes locally, including ERC/DRC and 30 tests
  (10 design, 8 purchasing, 10 CPL, 2 preview safety). The pinned container build
  was not rerun.
- Next action: correct U3/J7 and check every rotation in JLCPCB's placement preview,
  then continue the assembly checklist. No order, upload, commit or push was made.
