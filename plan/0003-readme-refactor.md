# Refactor Bullet Visual README

## Goal
Make the selected checkout's root README a structured, accurate operating guide while preserving its camera-source instructions and limitations.

## Implementation
- Reorganize the README into the project template's heading order, with a quick start before detailed USB and MIPI setup.
- Clarify that the documented `uv --package bullet-visual` commands run from the Bullet workspace root; this separate checkout is outside that workspace and uses workspace-only dependencies.
- Keep verified YAML fields, capture requirements, detector behavior, output protocol, source identity, and troubleshooting details. Replace the invalid relative workspace launcher link.

## Interfaces and scope
Documentation and plan metadata only. Do not change application code, YAML, dependencies, launch scripts, or the independent workspace copy. Do not claim physical camera capture was tested.

## Verification
Check headings, links, Markdown fences, shell syntax, profile loading, and current OpenCV GStreamer support against repository evidence.

## Status
Implemented and verified. Implementation commit: Pending (no commit requested).

## Verification results
- The README follows the required heading order; six local links resolve and Markdown fences are balanced.
- Six shell blocks passed `bash -n`. All three README YAML examples and the three supplied configuration profiles loaded through `bullet_visual.config.load_config`.
- Seven selected-checkout tests passed in the existing Bullet workspace environment. `git diff --check` passed.
- The existing workspace OpenCV build reports `GStreamer: NO`. The linked FLIR Boson integration page remains available. No camera capture or device setting was exercised.
- `bullet-visual --help` currently prints Click help and then raises `AttributeError`; this pre-existing CLI behavior was observed but is outside this documentation-only change.
