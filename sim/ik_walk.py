"""Very small inverse-kinematics walking demo for the Open Duck Mini lower body.

Run from the repo root:
    mjpython sim/ik_walk.py                    # macOS viewer
    python sim/ik_walk.py                      # Linux/Windows viewer
    python sim/ik_walk.py --check              # no window
    python sim/ik_walk.py --video              # render docs/videos/ik-walk.mp4

This is a kinematic, supported gait preview. It places the pelvis on a level
forward path and sets hip, knee and ankle joint angles directly; it does not
balance a free robot or command physical servos.
"""

import argparse
import math
import subprocess
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

from legs import gait_target, ik_joint_targets, load_legs

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIDEO = ROOT / "docs/videos/ik-walk.mp4"
DEFAULT_POSTER = ROOT / "docs/images/ik-walk-poster.png"
PHASE_SPEED = 2.0  # radians/second, one step cycle in pi seconds
STANCE_TRAVEL = gait_target(0)[0] - gait_target(math.pi)[0]
FORWARD_SPEED = STANCE_TRAVEL * PHASE_SPEED / math.pi


def walk_pose(model, data, seconds):
    """Set six pitch joints from two-link IK and advance the supported pelvis."""
    phase = PHASE_SPEED * seconds
    targets = ik_joint_targets(phase)
    data.qpos[:] = model.qpos0
    for name, angle in targets.items():
        joint = model.joint(name)
        if not joint.range[0] <= angle <= joint.range[1]:
            raise ValueError(f"{name} target {angle:.3f} exceeds its joint range")
        data.qpos[joint.qposadr[0]] = angle
    model.body_pos[model.body("base").id, 0] = FORWARD_SPEED * seconds
    mujoco.mj_forward(model, data)
    return targets


def check_walk():
    model, data = load_legs(keep_pelvis=True, floor=True)
    period = 2 * math.pi / PHASE_SPEED
    samples = []
    for t in np.linspace(0, 2 * period, 241):
        walk_pose(model, data, float(t))
        samples.append((float(t), data.site("left_foot").xpos.copy(),
                        data.site("right_foot").xpos.copy()))
    for side, column in (("left", 0), ("right", 1)):
        for cycle in (0, 1):
            stance = [(left, right)[column] for t, left, right in samples
                      if cycle <= t / period < cycle + 1
                      and ((PHASE_SPEED * t / (2 * math.pi) + (0 if side == "left" else 0.5)) % 1) < 0.5]
            if not stance:
                raise AssertionError(f"No {side} stance samples")
            x_range = np.ptp([p[0] for p in stance])
            z_range = np.ptp([p[2] for p in stance])
            assert x_range < 0.001, f"{side} stance foot slipped {x_range:.4f} m"
            assert z_range < 0.001, f"{side} stance foot moved vertically {z_range:.4f} m"
        heights = [(left, right)[column][2] for _, left, right in samples]
        assert max(heights) - min(heights) > 0.005, f"{side} foot did not lift"
    distance = FORWARD_SPEED * 2 * period
    assert distance > 0.09
    print(f"PASS: two cycles, pelvis advances {distance:.3f} m; stance feet stay within 1 mm")


def camera(seconds, *, center_x=None):
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = [FORWARD_SPEED * seconds + 0.02 if center_x is None else center_x,
                     0, 0.11]
    cam.distance = 0.58
    cam.azimuth = 135
    cam.elevation = -14
    return cam


def render_video(path, seconds=9.0, fps=24):
    model, data = load_legs(keep_pelvis=True, floor=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1280, 720
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
               "-i", "-", "-c:v", "libx264", "-crf", "21", "-preset", "medium",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        with mujoco.Renderer(model, height, width) as renderer:
            for frame in range(round(seconds * fps)):
                t = frame / fps
                walk_pose(model, data, t)
                renderer.update_scene(data, camera=camera(t, center_x=FORWARD_SPEED * seconds / 2))
                encoder.stdin.write(renderer.render().tobytes())
    finally:
        encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError("FFmpeg could not encode the IK walking video")
    if path == DEFAULT_VIDEO:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss",
                        str(seconds / 2), "-i", str(path), "-frames:v", "1", str(DEFAULT_POSTER)],
                       check=True)
    print(f"Saved {path}")


def show_viewer():
    model, data = load_legs(keep_pelvis=True, floor=True)
    walk_pose(model, data, 0)
    with mujoco.viewer.launch_passive(model, data) as viewer:
        start = time.monotonic()
        while viewer.is_running():
            seconds = time.monotonic() - start
            with viewer.lock():
                walk_pose(model, data, seconds)
                view = camera(seconds)
                viewer.cam.lookat[:] = view.lookat
                viewer.cam.distance = view.distance
                viewer.cam.azimuth = view.azimuth
                viewer.cam.elevation = view.elevation
            viewer.sync()
            time.sleep(1 / 60)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify foot stance, lift and joint limits without a window")
    parser.add_argument("--video", nargs="?", type=Path, const=DEFAULT_VIDEO, help="render an MP4; optional output path")
    args = parser.parse_args()
    if args.check:
        check_walk()
    elif args.video:
        render_video(args.video)
    else:
        show_viewer()


if __name__ == "__main__":
    main()
