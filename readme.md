# HDMI2C Monitor Controller

HDMI2C allows network control (via WiFi) of monitors connected to it via HDMI (via
[DDC]). This allows you to build your own tooling and control systems for your monitors,
rather than relying on awkward inconvient buttons and OSDs. Think of it as an API for
your monitors.

This repository contains the hardware design, made with [KiCAD]. The current
**rev2 XIAO ESP32-C6 carrier is CAD-checked but not physically tested**. Its
[prototype package](hardware/rev2/README.md) includes the BOM, schematic, assembly
drawings, Gerbers, and drills. Open the current project with KiCad 10.

The staged plan for a single-monitor board, XIAO ESP32-C6 migration, and ESPHome
firmware is in [PLAN.md](PLAN.md), including progress and handoff notes for future
sessions. The [upstream BOM and schematic][pages] describe the original revision,
not the current carrier.

## What could you build with this

- A physical brightness knob
- Switch a monitor's input when you wake up your desktop PC or connect your laptop
  to your dock
- IDK probably some other weird shit

## Features

- Seeed Studio XIAO ESP32-C6 with Wi-Fi; soldered castellated mounting
- The XIAO's USB-C power, native programming/logging, regulator, and boot/reset
- One HDMI port (`J7`, HDMI1) with:
  - TPD12S016PWR-based 3.3 V/5 V DDC translation and buffered HPD input
  - Independently controlled DDC enable and protected HDMI 5 V output
- Two small top-actuated buttons and four back-side diagnostic pads
- 42 × 24 mm two-layer carrier with antenna cutout and copper keepouts

Rev2 has 12 fitted components, including the purchased XIAO module, and a 68%
smaller bounding-box area than the 70 × 45 mm single-port rev1. Connector overhangs
are outside those dimensions. There are no mounting holes; provide enclosure
support and cable strain relief.

See the [hardware notes and pin mapping](docs/stage2-hardware.md) for design
decisions, resource provenance, verification, and outstanding physical tests.
ERC/DRC and schematic/PCB parity are clean; six design-regression tests pass.
Historical rev1 findings are recorded in [stage-1 validation](docs/stage1-validation.md).

## Firmware

Firmware is not included yet. [Stage 3 of the plan](PLAN.md#stage-3--esphome-firmware-over-wi-fi)
will add ESPHome firmware for Wi-Fi control of brightness and input selection,
targeting the XIAO ESP32-C6 carrier from stage 2.

## A word on monitor compatibility

Not all monitors implement DDC that well. Particularly of annoyance, some models I
tested would not listen to DDC commands on inputs that were not active, which, given
this project relies on you having a spare HDMI input which never carries any video, is
kind of a deal breaker.

### Known good monitors

- Dell U2515h — reported working by the original project's author with the
  original hardware/firmware; not yet retested with this XIAO/ESPHome redesign.

## Deferred ideas (outside the current plan)

- A larger carrier option with mounting holes
- Spare ESP32 IO broken out to headers for ease of hacking
- More ambitious, HDMI passthrough to allow use of the project without taking up a whole
  spare HDMI port.

## Is it that useful tho?

You can achieve the same thing without having to build your own hardware with a
Raspberry Pi 4. Support for dual monitor I2C (DDC) was added shortly before I started
this project - guess I didn't check enough :-). This is a much more accessible means to
achieve the same goal. However, if you want a more minimal solution that doesn't require
an entire embedded linux system, this project may be for you.

[DDC]: https://en.wikipedia.org/wiki/Display_Data_Channel
[KiCAD]: https://kicad.org
[pages]: https://wlcx.github.io/hdmi2c
