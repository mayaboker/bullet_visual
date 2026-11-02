# Bullet Visual

`bullet_visual` captures one configured image source, runs the shared
`bullet_perception` detector, and publishes `tracking/front/bbox` messages to
`bullet_app` on `tcp://127.0.0.1:5560`.

The source is selected in YAML. The process uses a latest-frame buffer so detector
latency cannot create an unbounded control delay. All commands below run from the
**workspace root**, which contains `projects/` and `tools/`.

## Choose and switch the image source

| Input | `source.type` | Configuration | Required source settings |
|---|---|---|---|
| Renderer images over ZMQ/shared memory | `zmq_shm` | [zmq.yaml](config/zmq.yaml) | Descriptor endpoint and exact image topic |
| USB camera through OpenCV | `usb` | [usb.yaml](config/usb.yaml) | Camera index or device path |
| MIPI camera through OpenCV/GStreamer | `mipi` | [mipi.yaml](config/mipi.yaml) | Platform-specific GStreamer pipeline |

To switch:

1. Stop the running `bullet_visual` process with Ctrl+C in its terminal. If the
   workspace launcher owns it, stop that launcher before starting a replacement.
2. Edit the selected configuration with the device or pipeline for your camera.
3. Start one of the commands below. Source selection is read at startup; there
   is no live source-switch command or automatic fallback.

```bash
# Renderer ZMQ/shared-memory input.
uv run --locked --package bullet-visual bullet-visual --config projects/bullet_visual/config/zmq.yaml

# USB camera input.
uv run --locked --package bullet-visual bullet-visual --config projects/bullet_visual/config/usb.yaml

# MIPI camera input.
uv run --locked --package bullet-visual bullet-visual --config projects/bullet_visual/config/mipi.yaml
```

All three choices publish detection results through ZMQ at
`tcp://127.0.0.1:5560`. USB/MIPI replace the image input; the output connection to
`bullet_app` stays the same. Run only one publisher on that endpoint. If changing
it, also change the application's `--visual-endpoint`.

The workspace [tools/run_all.sh](../../tools/run_all.sh) currently selects
`config/zmq.yaml` explicitly. It does not select USB/MIPI based on the connected
hardware. Use the standalone command above to select a physical camera; starting
Run all again will start its configured ZMQ source.

## ZMQ/shared-memory configuration

```yaml
source:
  # Renderer image descriptors with local shared-memory pixels.
  type: zmq_shm
  # Descriptor publisher endpoint; must match the renderer transport settings.
  endpoint: tcp://127.0.0.1:5556
  # Exact subscribed image topic; default is camera/front/image.
  topic: camera/front/image
output:
  # Detection publisher endpoint; default is tcp://127.0.0.1:5560.
  endpoint: tcp://127.0.0.1:5560
  # Image topic carried in detection packets; default is camera/front/image.
  image_topic: camera/front/image
```

The renderer must be running and publishing the expected descriptor format.
This adapter reads pixels from local POSIX shared memory, so the image producer
and consumer must share access to that memory. It does not accept arbitrary ZMQ
image payloads or provide remote-machine pixel transport.

## USB camera configuration and settings

The supplied `usb.yaml` uses camera index `0`. Change `source.device` to the
camera's video device path when several devices are present. A stable by-id
path avoids relying on the `/dev/videoN` numbering across reconnections.

```yaml
source:
  # Open a USB camera through OpenCV.
  type: usb
  # Integer camera index or device path; required for usb.
  # Example for the inspected Boson camera; replace with your own device path.
  device: /dev/v4l/by-id/usb-FLIR_Boson_281165-video-index0
output:
  # Detection publisher endpoint consumed by bullet_app.
  endpoint: tcp://127.0.0.1:5560
  # Image topic carried in detection packets.
  image_topic: camera/front/image
```

Inspect the connected devices and their supported modes:

```bash
ls -l /dev/v4l/by-id/
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext
v4l2-ctl -d /dev/video0 --get-fmt-video --get-parm
v4l2-ctl -d /dev/video0 --list-ctrls-menus
```

Use the **video-capture** node, rather than a metadata-only node. During the
Boson inspection, `video-index0` mapped to `/dev/video0` for video and
`video-index1` mapped to `/dev/video1` for metadata.

Camera controls depend on the device and driver. Use only names and values
reported by `--list-ctrls-menus` when applying controls with `v4l2-ctl --set-ctrl`.
For example, where the camera advertises this video mode, stop capture and
request 640 × 512 YU12 at 30 FPS:

```bash
v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=512,pixelformat=YU12 --set-parm=30
```

This command changes device state. Recheck `--get-fmt-video --get-parm` after
opening capture: OpenCV may renegotiate the format or frame rate. The application
currently opens the device using its negotiated defaults and does not enforce
those requested values on each startup.

USB YAML currently has **no width, height, FPS, pixel-format, exposure, gain,
focus or white-balance fields**. Unknown fields are rejected by the loader.
Camera controls are not exposed in the application UI or through MAVLink.

The inspected Boson exposed no standard V4L2 controls. Its command/control
settings use the FLIR GUI or SDK; see FLIR's
[Boson software integration guide](https://www.oem.flir.com/learn/thermal-integration-made-easy/software-integration---boson/).
Do not assume ordinary webcam exposure or focus controls exist on that device.

## MIPI camera configuration and settings

MIPI capture uses `cv2.CAP_GSTREAMER`. The supplied example uses `libcamerasrc`:

```yaml
source:
  # Open a MIPI camera through an OpenCV GStreamer pipeline.
  type: mipi
  # Example caps: 640x480 at 30 FPS. Use modes supported by your sensor/platform.
  # The pipeline must produce BGR frames and end in appsink.
  pipeline: "libcamerasrc ! video/x-raw,width=640,height=480,framerate=30/1 ! videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1"
output:
  # Detection publisher endpoint consumed by bullet_app.
  endpoint: tcp://127.0.0.1:5560
  # Image topic carried in detection packets.
  image_topic: camera/front/image
```

Select the source element, sensor and video modes for your hardware. Resolution
and frame rate are negotiated through the pipeline caps, not separate YAML
fields. Platform-specific camera controls belong in supported source-element
properties or the platform's camera-control tooling. `appsink` must deliver
8-bit, three-channel BGR images. The example keeps only the latest queued frame.

Check OpenCV support in the same uv environment used to run the application:

```bash
uv run --locked --package bullet-visual python -c "import cv2; print(cv2.getBuildInformation())"
gst-inspect-1.0 libcamerasrc
```

Look for `GStreamer: YES` in OpenCV's build information. At the time of this
documentation check, the workspace OpenCV build reports **`GStreamer: NO`**.
MIPI capture therefore requires a compatible OpenCV build and the appropriate
GStreamer source plugins before this example can run. Installing GStreamer tools
alone does not enable GStreamer support in an existing OpenCV build. A MIPI
camera and its platform-specific pipeline have not been capture-tested here.

## Detection and source identity

The current shared detector looks for red pixels in an 8-bit BGR image. Selecting
a camera does not change the detector. With a thermal camera, thresholds act on
the displayed palette colors; raw 16-bit `Y16` data needs a conversion step before
this detector can process it.

`zmq_shm` preserves Bullet v2 source identity. USB and MIPI emit schema-valid v1
identity using a generated session, sequence, and monotonic capture timestamp.
Those physical-camera packets do not originate with a simulator physics/episode
identity. Source selection alone does not provide camera calibration or guarantee
alignment with simulated sensor feedback.
