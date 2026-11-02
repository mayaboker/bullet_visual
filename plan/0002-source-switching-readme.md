# Document camera-source switching

## Goal
Explain how to select ZMQ/shared-memory, USB and MIPI capture and inspect camera
settings using the existing bullet_visual configuration and CLI.

## Implementation
- Expand the README with a source comparison, complete YAML examples and
  workspace-root launch commands for all three existing configuration files.
- Explain stopping/restarting the process, the common detection publisher and
  the run_all.sh launcher currently selecting zmq.yaml.
- Document USB device discovery/stable paths, V4L2 inspection and current YAML
  setting limits. Include the connected Boson path as a replaceable example.
- Document platform-specific MIPI GStreamer pipelines, BGR appsink output and
  checking OpenCV/plugin support. Explain detector and source identity limits.

## Interfaces and scope
Documentation only. Do not change source code, YAML files, launch scripts,
dependencies, camera controls or runtime state. No hardware capture is included.
The follow-up user request authorizes committing the documentation and recording
its implementation hash; no push is included in this commit task.

## Verification
Check local documentation links, shell command paths and Markdown fences. Load
existing profiles and documented YAML examples through the actual loader. Check
OpenCV build information without opening cameras. Do not claim hardware capture
or camera-setting application has been tested.

## Status
Implemented and committed; documentation verification passed.

## Verification results
- All three README YAML examples and all three existing configuration profiles
  loaded successfully through bullet_visual.config.load_config.
- All documented shell blocks passed bash -n without executing capture or
  device-setting commands. Local Markdown links and configuration command paths
  exist; Markdown fences are balanced. git diff --check passed.
- OpenCV build information confirms GStreamer: NO in the current shared uv
  environment, matching the documented MIPI prerequisite.
- No hardware capture or control-setting application was performed. Existing
  source code, camera profiles, launch scripts and dependency files are unchanged.
- Only README.md, this plan and the project plan menu were edited. No runtime
  tests were needed for the documentation-only update.

## Implementation commit
`6249e06027e25daf5e41246f757a8eea873a2af8`
