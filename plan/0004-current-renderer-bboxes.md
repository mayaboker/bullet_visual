# Current renderer bounding boxes

Status: Pending
Implementation commit: Pending

Goal: Publish red-target bounding boxes from the current Godot shared-memory image stream.

Implementation: Replace legacy image reader and schema dependency with current transport libraries, retain frame identity and host measurement time, and publish bbox or null packets for App.

Interfaces: `tracking/front/bbox` on configured ZeroMQ endpoint with image identity, dimensions, bbox, and monotonic measurement timestamp.

Verification: Descriptor and publisher tests including absent target and stale inputs.

Verification outcome: Visual focused tests and isolated renderer-to-Visual bbox transport passed; renderer native build and export passed.

Follow-up: When a still-running older renderer publishes v3 descriptors without `host_capture_ns`, Visual now raises an actionable restart error instead of silently reporting zero captures. A focused compatibility test passed.

Scope/defaults: Existing USB/MIPI sources remain supported.
