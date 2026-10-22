"""View only the Open Duck Mini v2 leg mechanisms in MuJoCo.

Run from the repository root: mjpython sim/legs.py (macOS), python sim/legs.py (Linux/Windows).
Use --gait to preview alternating steps with a simple planar two-link IK model.
Use --preview PATH to render a still image without opening a viewer.
"""

import argparse
import math
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

HERE = Path(__file__).resolve().parent
MODEL = HERE / "model" / "open_duck_mini_v2.xml"
LEG_NAMES = (
    "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
    "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
)
LINK_LENGTH = 0.07865  # hip-to-knee and knee-to-ankle, from the MuJoCo model (metres)


def two_link_ik(x, z, upper=LINK_LENGTH, lower=LINK_LENGTH):
    """Hip and knee for an ankle target x forward, z downward from the hip."""
    distance_squared = x * x + z * z
    if not (upper - lower) ** 2 < distance_squared < (upper + lower) ** 2:
        raise ValueError("Ankle target is outside the two-link workspace")
    knee = math.acos((distance_squared - upper * upper - lower * lower) / (2 * upper * lower))
    hip = math.atan2(x, -z) - math.atan2(lower * math.sin(knee), upper + lower * math.cos(knee))
    return hip, knee


def gait_target(phase):
    """Small stance sweep and raised swing, returning the ankle target in metres."""
    cycle = (phase / (2 * math.pi)) % 1
    if cycle < 0.5:
        return 0.018 - 0.072 * cycle, -0.145
    swing = (cycle - 0.5) * 2
    return -0.018 + 0.036 * swing, -0.145 + 0.012 * math.sin(math.pi * swing)


def ik_joint_targets(phase):
    """Planar IK targets for alternating feet, with mirrored hip pitch joints."""
    left_hip, left_knee = two_link_ik(*gait_target(phase))
    right_hip, right_knee = two_link_ik(*gait_target(phase + math.pi))
    return {
        "left_hip_pitch": left_hip, "left_knee": left_knee,
        "left_ankle": -left_hip - left_knee,
        "right_hip_pitch": -right_hip, "right_knee": right_knee,
        "right_ankle": -right_hip - right_knee,
    }


def load_legs(*, keep_pelvis=False, floor=False):
    """Keep the leg branches and position actuators on a fixed base."""
    root = ET.parse(MODEL).getroot()
    visual = ET.Element("visual")
    ET.SubElement(visual, "headlight", ambient="0.55 0.55 0.55", diffuse="0.55 0.55 0.55")
    ET.SubElement(visual, "global", offwidth="1920", offheight="1080")
    root.insert(2, visual)
    ET.SubElement(root.find("asset"), "texture", type="skybox", builtin="gradient", rgb1="0.82 0.88 0.95", rgb2="0.82 0.88 0.95", width="512", height="512")
    world = root.find("worldbody")
    base = world.find("body")
    trunk = base.find("body")
    base.remove(base.find("freejoint"))
    for child in list(base):
        if child.tag == "site":
            base.remove(child)
    for child in list(trunk):
        pelvis = child.tag == "geom" and child.get("mesh") in {"trunk_bottom", "trunk_top"}
        if (child.tag in {"geom", "site"} and not (keep_pelvis and pelvis)) or (child.tag == "body" and child.get("name") == "neck_pitch_assembly"):
            trunk.remove(child)
    if keep_pelvis:
        for body in trunk.iter("body"):
            for geom in list(body.findall("geom")):
                if geom.get("mesh") in {"left_cache", "right_cache"}:
                    body.remove(geom)
    if floor:
        asset = root.find("asset")
        ET.SubElement(asset, "texture", name="walk_grid", type="2d", builtin="checker",
                      rgb1="0.22 0.25 0.28", rgb2="0.16 0.19 0.22", width="512", height="512")
        ET.SubElement(asset, "material", name="walk_floor", texture="walk_grid", texrepeat="24 24")
        ET.SubElement(world, "geom", type="plane", name="floor", pos="0 0 0.018",
                      size="2 2 0.01", material="walk_floor", contype="0", conaffinity="0")
    sensor = root.find("sensor")
    if sensor is not None:
        root.remove(sensor)
    actuator = root.find("actuator")
    for motor in list(actuator):
        if motor.get("name") not in LEG_NAMES:
            actuator.remove(motor)
    compiler = root.find("compiler")
    compiler.set("meshdir", str(MODEL.parent / "assets"))
    xml = ET.tostring(root, encoding="unicode")
    model = mujoco.MjModel.from_xml_string(xml)
    model.opt.gravity[:] = 0  # the hip fixture is fixed; this is a mechanism viewer
    data = mujoco.MjData(model)
    assert [model.actuator(i).name for i in range(model.nu)] == list(LEG_NAMES)
    return model, data


def pose(model, data, phase, gait=False):
    """A small symmetric bend makes the four visible leg links easy to distinguish."""
    if gait:
        targets = ik_joint_targets(phase)
    else:
        bend = 0.2 + 0.12 * math.sin(phase)
        targets = {
            "left_hip_pitch": -0.35, "left_knee": 0.7 + bend,
            "left_ankle": -0.35 - bend, "right_hip_pitch": 0.35,
            "right_knee": 0.7 + bend, "right_ankle": -0.35 - bend,
        }
    for i, name in enumerate(LEG_NAMES):
        data.ctrl[i] = targets.get(name, 0)
    mujoco.mj_step(model, data)


def camera():
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = [0, 0, 0.12]
    cam.distance = 0.48
    cam.azimuth = 140
    cam.elevation = -15
    return cam


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path, help="write a PNG still instead of opening the viewer")
    parser.add_argument("--gait", action="store_true", help="alternate small IK foot steps in the fixed-hip viewer")
    args = parser.parse_args()
    model, data = load_legs()
    for _ in range(150):
        pose(model, data, 0, args.gait)
    if args.preview:
        with mujoco.Renderer(model, height=480, width=640) as renderer:
            renderer.update_scene(data, camera=camera())
            pixels = renderer.render()
        from PIL import Image
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.asarray(pixels)).save(args.preview)
        print(f"Saved {args.preview}")
        return
    print("Showing the fixed-hip leg mechanisms. Close the viewer to quit.")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.lookat[:] = camera().lookat
        viewer.cam.distance = camera().distance
        viewer.cam.azimuth = camera().azimuth
        viewer.cam.elevation = camera().elevation
        start = time.monotonic()
        while viewer.is_running():
            pose(model, data, (time.monotonic() - start) * 2, args.gait)
            viewer.sync()
            time.sleep(model.opt.timestep)


if __name__ == "__main__":
    main()
