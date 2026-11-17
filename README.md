# Bullet Visual

Bullet Visual captures images from one configured source, detects the largest qualifying red target with `bullet_perception`, and publishes bounding boxes for Bullet App.

## Overview

This service separates image capture and detection from flight control. It accepts renderer images through local ZMQ/shared memory, a USB camera through OpenCV, or a MIPI camera through an OpenCV GStreamer pipeline. It publishes `tracking/front/bbox` over ZMQ to Bullet App, by default at `tcp://127.0.0.1:5560`.

The run commands below apply to a **Bullet uv workspace** containing `projects/bullet_visual`, `projects/bullet_msgs`, and `projects/bullet_perception`. This independent checkout is currently outside that workspace; running those commands from the workspace root uses its workspace-member copy. This checkout's `pyproject.toml` declares `bullet-msgs` and `bullet-perception` as workspace dependencies, so it is not independently installable with `uv sync` as configured.

## Features

- Select one of three image inputs in YAML: renderer ZMQ/shared memory, USB, or MIPI.
- Keep only the newest captured frame when detection falls behind, avoiding an unbounded image backlog.
- Publish schema-validated bounding boxes, including `null` when no target is found. The output endpoint is the same for all input types.

## Architecture

```mermaid
flowchart LR
    A[Renderer ZMQ/shared memory<br/>USB camera<br/>MIPI camera] --> B[Capture thread]
    B --> C[Latest-frame slot]
    C --> D[Detection thread<br/>bullet_perception.detect_bbox]
    D --> E[ZMQ bbox publisher<br/>tracking/front/bbox]
    E --> F[Bullet App]
```

The capture adapter produces 8-bit, three-channel BGR images. The detection thread reads the latest frame, runs the shared detector, and publishes a bounding-box packet. Capture and detection errors stop the runtime; source switching and automatic fallback are not implemented.

## Requirements

- Python 3.12 or newer and `uv`, using a Bullet workspace that includes this package and its workspace dependencies. Runtime dependencies are declared in [pyproject.toml](pyproject.toml).
- For `zmq_shm`: a renderer publishing the expected image descriptors and accessible local POSIX shared memory. This adapter does not accept arbitrary ZMQ image payloads or transport pixels between machines.
- For `usb`: an OpenCV-readable video capture device. The Linux device-inspection commands below additionally require `v4l2-ctl`.
- For `mipi`: a sensor-specific GStreamer pipeline, its source plugins, and an OpenCV build with GStreamer support. The currently inspected workspace OpenCV build reports `GStreamer: NO`; installing GStreamer tools alone does not change that build.

## Installation

From the root of a Bullet workspace containing this package and its locked dependencies:

```bash
uv sync --locked --package bullet-visual
```

The standalone `/home/user/projects/bullet_visual` checkout has no workspace root or lockfile of its own. To run this checkout's code, place it in a uv workspace with the declared `bullet-msgs` and `bullet-perception` members and resolve that workspace's lockfile. The existing `/home/user/workspaces/bullet` workspace already has a separate `projects/bullet_visual` member.

## Quick Start

Start the renderer image producer and Bullet App as needed, then run this command **from the Bullet workspace root**:

```bash
uv run --locked --package bullet-visual bullet-visual --config projects/bullet_visual/config/zmq.yaml
```

The process logs captured, processed, dropped, no-target, and publish-drop counts. With a compatible renderer source, it publishes bounding-box packets on `tcp://127.0.0.1:5560`. Stop it with Ctrl+C. Bullet Visual does not start the renderer or Bullet App.

## Usage

Choose exactly one source by passing its configuration file. Run these commands from the workspace root:

| Input | Command |
| --- | --- |
| Renderer ZMQ/shared memory | `uv run --locked --package bullet-visual bullet-visual --config projects/bullet_visual/config/zmq.yaml` |
| USB camera | `uv run --locked --package bullet-visual bullet-visual --config projects/bullet_visual/config/usb.yaml` |
| MIPI camera | `uv run --locked --package bullet-visual bullet-visual --config projects/bullet_visual/config/mipi.yaml` |

To switch sources, stop the running process, edit or select the new configuration, and start one command. If the workspace launcher owns Bullet Visual, stop that launcher first. The workspace's `tools/run_all.sh` explicitly starts the `zmq.yaml` source; it does not choose USB or MIPI based on connected hardware. Starting it again will start that configured ZMQ source.

Run only one publisher on the output endpoint. All three source choices publish through ZMQ at `tcp://127.0.0.1:5560` by default. If you change `output.endpoint`, also change Bullet App's `--visual-endpoint` in the workspace version that consumes these messages.

## Configuration

The supplied profiles are [zmq.yaml](config/zmq.yaml), [usb.yaml](config/usb.yaml), and [mipi.yaml](config/mipi.yaml). The loader rejects unknown YAML fields and requires a source and output section.

| Field | Default or requirement | Meaning |
| --- | --- | --- |
| `source.type` | Required: `zmq_shm`, `usb`, or `mipi` | Selects the capture adapter. |
| `source.endpoint` | Required for `zmq_shm` | Renderer descriptor PUB endpoint. |
| `source.topic` | `camera/front/image` | Exact image topic subscribed to by `zmq_shm`. |
| `source.device` | Required for `usb` | OpenCV camera index or device path. |
| `source.pipeline` | Required for `mipi` | GStreamer pipeline ending in a BGR `appsink`. |
| `output.endpoint` | `tcp://127.0.0.1:5560` | ZMQ PUB endpoint consumed by Bullet App. It must differ from `source.endpoint` for `zmq_shm`. |
| `output.image_topic` | `camera/front/image` | Image topic included in bounding-box packets. |

### Renderer ZMQ/shared memory

```yaml
source:
  # Select descriptors with pixels in local shared memory.
  type: zmq_shm
  # Renderer descriptor PUB endpoint.
  endpoint: tcp://127.0.0.1:5556
  # Exact image topic to subscribe to.
  topic: camera/front/image
output:
  # Detection PUB endpoint consumed by Bullet App.
  endpoint: tcp://127.0.0.1:5560
  # Image topic written into bbox packets.
  image_topic: camera/front/image
```

The renderer must publish the expected descriptor format, and the producer and consumer must share access to the POSIX shared-memory pixels.

### USB camera

The supplied `usb.yaml` selects camera index `0`. For multiple cameras, set `source.device` to a stable by-id video path. The following alternative is an example from an inspected FLIR Boson; replace it with your own device path:

```yaml
source:
  # Select an OpenCV USB capture device.
  type: usb
  # Camera index or video device path, such as the inspected Boson video node.
  device: /dev/v4l/by-id/usb-FLIR_Boson_281165-video-index0
output:
  # Detection PUB endpoint consumed by Bullet App.
  endpoint: tcp://127.0.0.1:5560
  # Image topic written into bbox packets.
  image_topic: camera/front/image
```

Inspect connected devices and supported modes before changing camera settings:

```bash
ls -l /dev/v4l/by-id/
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext
v4l2-ctl -d /dev/video0 --get-fmt-video --get-parm
v4l2-ctl -d /dev/video0 --list-ctrls-menus
```

Use the **video-capture** node, not a metadata-only node. In the inspected Boson setup, `video-index0` mapped to `/dev/video0` for video and `video-index1` to `/dev/video1` for metadata. Camera controls depend on the device and driver; apply only values reported by `--list-ctrls-menus`. Where supported, stop capture and request this mode, then recheck it after OpenCV opens the device:

```bash
v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=512,pixelformat=YU12 --set-parm=30
v4l2-ctl -d /dev/video0 --get-fmt-video --get-parm
```

OpenCV may renegotiate the format or frame rate. The application opens the device with negotiated defaults and does not enforce width, height, FPS, pixel format, exposure, gain, focus, or white balance from YAML; unknown fields are rejected. The inspected Boson exposed no standard V4L2 controls. Its command settings use the FLIR GUI or SDK; see the [Boson software integration guide](https://www.oem.flir.com/learn/thermal-integration-made-easy/software-integration---boson/).

### MIPI camera

The supplied `mipi.yaml` demonstrates a `libcamerasrc` pipeline. Adapt the source element, caps, and sensor settings to your hardware:

```yaml
source:
  # Select OpenCV's GStreamer capture backend.
  type: mipi
  # Produce BGR frames in appsink; keep only the latest queued frame.
  pipeline: "libcamerasrc ! video/x-raw,width=640,height=480,framerate=30/1 ! videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1"
output:
  # Detection PUB endpoint consumed by Bullet App.
  endpoint: tcp://127.0.0.1:5560
  # Image topic written into bbox packets.
  image_topic: camera/front/image
```

Resolution and frame rate are negotiated through the pipeline caps, not separate YAML fields. Camera controls belong in supported source-element properties or platform tooling. The pipeline must deliver 8-bit, three-channel BGR frames to `appsink`. Check the OpenCV build and plugin in the same workspace environment used for capture:

```bash
uv run --locked --package bullet-visual python -c "import cv2; print(cv2.getBuildInformation())"
gst-inspect-1.0 libcamerasrc
```

Look for `GStreamer: YES` in OpenCV's build information. The inspected workspace build reports `GStreamer: NO`, so this MIPI example needs a compatible OpenCV build and the appropriate source plugins. A MIPI camera and this pipeline have not been capture-tested here.

### Detection and packet identity

The detector looks for red pixels in an 8-bit BGR image. Selecting a new camera does not change the detector. With a thermal camera, thresholds apply to displayed palette colors; raw 16-bit `Y16` frames need conversion before detection.

`zmq_shm` preserves Bullet v2 source identity. USB and MIPI emit schema-valid v1 identity with a generated session, sequence, and monotonic capture timestamp. Physical-camera packets do not have simulator physics or episode identity. Source selection does not provide camera calibration or guarantee alignment with simulated sensor feedback.

## Project Structure

```text
bullet_visual/
├── config/                 # Example source profiles
├── src/bullet_visual/      # CLI, configuration, capture, runtime, publication
├── tests/                  # Configuration and publisher tests
├── plan/                   # Implementation records
├── pyproject.toml
└── README.md
```

## Development

Work in a Bullet uv workspace containing this package and its workspace dependencies. The package uses Click for its CLI, OpenCV for camera capture, `bullet_perception` for detection, and pyzmq for image-descriptor input and bbox output. No formatter or linter command is configured in this checkout.

## Testing

From the Bullet workspace root:

```bash
uv run --locked --package bullet-visual pytest -q projects/bullet_visual/tests
```

These tests cover configuration and publication behavior. They do not open a physical USB or MIPI camera.

## Documentation

The [configuration profiles](config/) show the supported source fields. The [plan index](plan/README.md) records prior implementation and documentation changes. The workspace's `tools/run_all.sh` is the integration launcher; this standalone checkout does not contain that script.

## Troubleshooting

- **No bounding boxes:** Confirm the image source is running, the ZMQ descriptor endpoint and exact topic match, the shared-memory pixels are accessible, and Bullet App connects to the configured output endpoint. A frame with no qualifying target publishes `bbox: null`.
- **USB capture fails:** Check the selected video-capture node with `v4l2-ctl`; metadata nodes cannot provide frames to OpenCV. Confirm device access and supported formats.
- **MIPI capture fails:** Check `gst-inspect-1.0 libcamerasrc` and verify that the active OpenCV build reports `GStreamer: YES`. The inspected workspace build currently reports `NO`.
- **Standalone `uv sync` fails:** This checkout declares two `workspace = true` dependencies. Run it as a member of a Bullet uv workspace containing `bullet_msgs` and `bullet_perception`, or adjust package sources as a separate packaging change.
- **A source stops returning frames:** The runtime raises an error and stops. Restart it after fixing the source; it does not switch to another input automatically.

## Roadmap

No roadmap is declared in this repository.

## Contributing

A project-specific contribution process is not specified. Run the tests for changes to capture, configuration, or publication behavior.

## License

No license file or license metadata is present in this checkout.
