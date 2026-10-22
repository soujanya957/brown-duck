"""Walk the lower-body URDF with a supported, two-link IK gait in MuJoCo.

From the repository root, run ``mjpython sim/urdf_walk.py`` on macOS or
``python sim/urdf_walk.py`` on Linux/Windows. Use ``--check`` without a window.
The pelvis follows a prescribed path; this is not a balance or servo controller.
"""

import argparse
import math
import subprocess
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

from legs import gait_target, ik_joint_targets, two_link_ik

URDF = Path(__file__).resolve().parent / "model/lower_body.urdf"
ROOT = URDF.parents[2]
DEFAULT_VIDEO = ROOT / "docs/videos/urdf-walk.mp4"
DEFAULT_POSTER = ROOT / "docs/images/urdf-walk-poster.png"
ROOT_HEIGHT = 0.1839  # puts the printed foot soles at the visual floor in stance
PHASE_SPEED = 2.0
FORWARD_SPEED = (gait_target(0)[0] - gait_target(math.pi)[0]) * PHASE_SPEED / math.pi


def load_model():
    """Import the actual URDF and add a visual floor to the MuJoCo scene."""
    spec = mujoco.MjSpec.from_file(str(URDF))
    spec.add_texture(type=mujoco.mjtTexture.mjTEXTURE_SKYBOX,
                     builtin=mujoco.mjtBuiltin.mjBUILTIN_GRADIENT,
                     rgb1=[0.82, 0.88, 0.95], rgb2=[0.82, 0.88, 0.95],
                     width=512, height=512)
    spec.add_texture(name="walk_grid", type=mujoco.mjtTexture.mjTEXTURE_2D,
                     builtin=mujoco.mjtBuiltin.mjBUILTIN_CHECKER,
                     rgb1=[0.24, 0.28, 0.33], rgb2=[0.18, 0.22, 0.26],
                     width=512, height=512)
    spec.add_material(name="walk_floor", textures=["walk_grid"], texrepeat=[24, 24])
    spec.worldbody.add_geom(name="floor", type=mujoco.mjtGeom.mjGEOM_PLANE,
                            size=[2, 2, 0.01], material="walk_floor",
                            contype=0, conaffinity=0)
    for index in range(-10, 11):
        spec.worldbody.add_geom(name=f"stride_mark_{index}", type=mujoco.mjtGeom.mjGEOM_BOX,
                                pos=[index * 0.1, 0, 0.0002], size=[0.0008, 0.6, 0.0002],
                                rgba=[0.35, 0.40, 0.45, 1], contype=0, conaffinity=0)
    model = spec.compile()
    model.vis.headlight.ambient[:] = [0.55, 0.55, 0.55]
    model.vis.headlight.diffuse[:] = [0.8, 0.8, 0.8]
    model.vis.global_.offwidth = 1920
    model.vis.global_.offheight = 1080
    data = mujoco.MjData(model)
    return model, data


def pose(model, data, seconds):
    """Set the ten leg joints and advance the supported pelvis."""
    data.qpos[:] = model.qpos0
    for name, angle in ik_joint_targets(PHASE_SPEED * seconds).items():
        joint = model.joint(name)
        if not joint.range[0] <= angle <= joint.range[1]:
            raise ValueError(f"{name} target {angle:.3f} exceeds its joint range")
        data.qpos[joint.qposadr[0]] = angle
    model.body_pos[model.body("trunk_assembly").id] = [FORWARD_SPEED * seconds, 0, ROOT_HEIGHT]
    mujoco.mj_forward(model, data)


def target_pose(model, data, x, z):
    """Show a single IK foot target on both legs before trying the gait."""
    hip, knee = two_link_ik(x, z)
    targets = {"left_hip_pitch": hip, "left_knee": knee,
               "left_ankle": -hip - knee, "right_hip_pitch": -hip,
               "right_knee": knee, "right_ankle": -hip - knee}
    data.qpos[:] = model.qpos0
    for name, angle in targets.items():
        joint = model.joint(name)
        if not joint.range[0] <= angle <= joint.range[1]:
            raise ValueError(f"{name} target {angle:.3f} exceeds its joint range")
        data.qpos[joint.qposadr[0]] = angle
    model.body_pos[model.body("trunk_assembly").id] = [0, 0, ROOT_HEIGHT]
    mujoco.mj_forward(model, data)
    print(f"Foot target relative to hip: x={x:+.3f} m, z={z:+.3f} m")
    print(f"Left hip {math.degrees(hip):+.1f}°, knee {math.degrees(knee):+.1f}°, "
          f"ankle {math.degrees(-hip-knee):+.1f}°")


def check():
    model, data = load_model()
    assert model.njnt == 10, f"Expected ten leg joints, found {model.njnt}"
    period = 2 * math.pi / PHASE_SPEED
    samples = []
    for t in np.linspace(0, 2 * period, 241):
        pose(model, data, float(t))
        samples.append((float(t), data.body("left_foot").xpos.copy(),
                        data.body("right_foot").xpos.copy()))
    for side, column, phase_offset in (("left", 1, 0), ("right", 2, math.pi)):
        for cycle in (0, 1):
            stance = [sample[column] for sample in samples
                      if cycle <= sample[0] / period < cycle + 1
                      and ((PHASE_SPEED * sample[0] + phase_offset) % (2 * math.pi)) < math.pi]
            assert stance, f"No {side} stance samples"
            for axis in (0, 2):
                assert np.ptp([p[axis] for p in stance]) < 0.001, f"{side} stance foot slipped"
        heights = [sample[column][2] for sample in samples]
        assert max(heights) - min(heights) > 0.005, f"{side} swing foot did not lift"
    assert FORWARD_SPEED * 2 * period > 0.09
    print("PASS: URDF loads, ten leg joints move, stance feet stay within 1 mm, "
          f"pelvis advances {FORWARD_SPEED * 2 * period:.3f} m")


def viewer():
    model, data = load_model()
    pose(model, data, 0)
    print("Showing the URDF lower-body IK walk. Close the viewer to quit.")
    with mujoco.viewer.launch_passive(model, data) as window:
        start = time.monotonic()
        while window.is_running():
            seconds = time.monotonic() - start
            with window.lock():
                pose(model, data, seconds)
                window.cam.lookat[:] = [FORWARD_SPEED * seconds, 0, 0.10]
                window.cam.distance = 0.58
                window.cam.azimuth = 135
                window.cam.elevation = -14
            window.sync()
            time.sleep(1 / 60)


def target_viewer(x, z):
    model, data = load_model()
    target_pose(model, data, x, z)
    print("Showing the static IK target. Close the viewer to quit.")
    with mujoco.viewer.launch_passive(model, data) as window:
        window.cam.lookat[:] = [0, 0, 0.10]
        window.cam.distance = 0.58
        window.cam.azimuth = 135
        window.cam.elevation = -14
        while window.is_running():
            window.sync()
            time.sleep(1 / 60)


def render_video(path, seconds=9.0, fps=24):
    """Render the URDF gait with a fixed camera so forward travel is visible."""
    model, data = load_model()
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1280, 720
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
               "-i", "-", "-c:v", "libx264", "-crf", "21", "-preset", "medium",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = [FORWARD_SPEED * seconds / 2, 0, 0.10]
    camera.distance = 0.58
    camera.azimuth = 135
    camera.elevation = -14
    try:
        with mujoco.Renderer(model, height, width) as renderer:
            for frame in range(round(seconds * fps)):
                pose(model, data, frame / fps)
                renderer.update_scene(data, camera=camera)
                encoder.stdin.write(renderer.render().tobytes())
    finally:
        encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError("FFmpeg could not encode the URDF walking video")
    if path == DEFAULT_VIDEO:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-ss", str(seconds / 2), "-i", str(path), "-frames:v", "1",
                        str(DEFAULT_POSTER)], check=True)
    print(f"Saved {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the URDF gait without a window")
    parser.add_argument("--video", nargs="?", type=Path, const=DEFAULT_VIDEO,
                        help="render an MP4; optional output path (requires FFmpeg)")
    parser.add_argument("--target", nargs=2, type=float, metavar=("X", "Z"),
                        help="show a static IK target in metres relative to the hip")
    args = parser.parse_args()
    if args.target and (args.check or args.video):
        parser.error("--target cannot be combined with --check or --video")
    if args.check:
        check()
    elif args.video:
        render_video(args.video)
    elif args.target:
        target_viewer(*args.target)
    else:
        viewer()


if __name__ == "__main__":
    main()
