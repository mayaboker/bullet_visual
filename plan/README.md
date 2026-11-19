# Plans

| Plan | Description | Status | Implementation commit |
| --- | --- | --- | --- |
| [0001 Visual capture and bbox ingress](0001-visual-capture-and-bbox-ingress.md) | Move image capture/detection into bullet_visual and feed bullet_app through a dedicated ZMQ ingress. | Complete | `91d45b9` |
| [0002 Source switching README](0002-source-switching-readme.md) | Explain ZMQ, USB and MIPI configuration, switching and camera-setting limits. | Implemented; examples, links and shell syntax verified | `6249e06027e25daf5e41246f757a8eea873a2af8` |
| [0003 README refactor](0003-readme-refactor.md) | Reorganize the operating guide and clarify its workspace prerequisite. | Implemented; documentation checks passed | Pending (no commit requested) |
| [0004 Current renderer bounding boxes](0004-current-renderer-bboxes.md) | Read v3 renderer images and publish host-stamped red-target bboxes. | Pending; focused tests passed | Pending |
| [0005 VS Code ZMQ run task](0005-vscode-zmq-run-task.md) | Start bullet_visual with config/zmq.yaml from VS Code. | Pending; task and config verified | Pending |
| [0006 Fid-tagged bbox packets](0006-fid-bbox.md) | Add image fid to local detection packets. | Implemented; tests and live smoke passed | `542f74e65ab6436c29aa6c2e440dc619ac007bdf` |
