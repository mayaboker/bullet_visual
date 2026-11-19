# Fid-tagged bbox packets

Status: Implemented; tests and live smoke passed
Implementation commit: Pending

Goal: Carry the renderer image fid with every local detection.

Implementation: Add fid from v3 image header to Visual's bbox packet; preserve existing session, sequence, and capture metadata. Other camera sources use their frame sequence as fid.

Interface: `tracking/front/bbox` gains integer `fid`.

Verification: Publisher and runtime tests for detected and no-target frames.

Scope: Visual still publishes over its existing ZMQ endpoint.

Verification outcome: Nine Visual tests passed; the live target stack reported processed frames and no publish drops.
