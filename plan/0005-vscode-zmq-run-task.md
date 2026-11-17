# VS Code ZMQ run task

Status: Pending
Implementation commit: Pending

Goal: Start bullet_visual with its existing ZMQ camera configuration from VS Code.

Implementation: Add a play-icon task that runs `uv run --locked bullet-visual --config config/zmq.yaml` from the bullet_visual project folder. Document when to use the standalone task.

Interface: VS Code task **Bullet: Run visual (ZMQ)**; no application or protocol changes.

Verification: Parse the task JSON, check the referenced config and CLI command, and run `git diff --check`.

Verification outcome: Task JSON parsed, ZMQ config loaded with expected endpoints, and `git diff --check` passed.

Scope/defaults: Use the current `config/zmq.yaml` endpoints. The target-scene launcher already starts visual and should not run alongside this standalone task.
