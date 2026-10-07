"""Headless smoke test for teleop.py: no window, no GPU.

Replaces mujoco.viewer.launch_passive with a dummy viewer, presses W at 2 s,
A at 8 s and Space at 12 s through the real key callback, and checks the duck
walked forward and did not fall.

    python sim/test_headless.py
"""

import contextlib
import sys
import time
from pathlib import Path

import mujoco
import mujoco.viewer

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teleop  # noqa: E402

SIM_SECONDS = 16.0
KEY_SCHEDULE = [(2.0, teleop.KEY_W), (8.0, teleop.KEY_A), (12.0, teleop.KEY_SPACE)]
MIN_FORWARD_M = 0.2
MIN_HEIGHT_M = 0.12


def main():
    duck = teleop.MjInfer(
        teleop.HERE / "model" / "scene_flat_terrain.xml",
        teleop.HERE / "data" / "polynomial_coefficients.pkl",
        teleop.HERE / "policies" / "BEST_WALK_ONNX_2.onnx",
        standing=False,
    )
    data = duck.data
    pending = list(KEY_SCHEDULE)
    hooks = {}
    log = {"start": data.qpos[0:3].copy(), "min_z": float("inf"), "at_key": []}

    class DummyViewer:
        def is_running(self):
            return data.time < SIM_SECONDS

        def sync(self):
            log["min_z"] = min(log["min_z"], float(data.qpos[2]))
            if pending and data.time >= pending[0][0]:
                t, key = pending.pop(0)
                log["at_key"].append((t, data.qpos[0:3].copy()))
                hooks["key_callback"](key)

        def lock(self):
            return contextlib.nullcontext()

    @contextlib.contextmanager
    def fake_launch_passive(model, d, key_callback=None, **kwargs):
        hooks["key_callback"] = key_callback
        yield DummyViewer()

    mujoco.viewer.launch_passive = fake_launch_passive
    teleop.time.sleep = lambda s: None  # run faster than real time

    wall = time.time()
    duck.run()
    end = data.qpos[0:3].copy()

    print(f"\nsimulated {data.time:.1f} s in {time.time() - wall:.1f} s wall time")
    print(f"start      x={log['start'][0]:+.3f} y={log['start'][1]:+.3f} z={log['start'][2]:.3f}")
    for t, p in log["at_key"]:
        print(f"t={t:4.1f} s   x={p[0]:+.3f} y={p[1]:+.3f} z={p[2]:.3f}")
    print(f"end        x={end[0]:+.3f} y={end[1]:+.3f} z={end[2]:.3f}")
    print(f"min trunk height {log['min_z']:.3f} m")

    forward = log["at_key"][1][1][0] - log["at_key"][0][1][0]  # x gained while W held
    print(f"forward progress during W: {forward:+.3f} m")
    assert forward >= MIN_FORWARD_M, f"walked only {forward:.3f} m forward"
    assert log["min_z"] > MIN_HEIGHT_M, f"trunk dropped to {log['min_z']:.3f} m (fell)"
    print("PASS")


if __name__ == "__main__":
    main()
