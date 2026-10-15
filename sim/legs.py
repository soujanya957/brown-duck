"""View only the Open Duck Mini v2 leg mechanisms in MuJoCo.

Run from the repository root: mjpython sim/legs.py (macOS), python sim/legs.py (Linux/Windows).
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


def load_legs():
    """Keep the original leg branches and position actuators, anchored at the invisible hip."""
    root = ET.parse(MODEL).getroot()
    visual = ET.Element("visual")
    ET.SubElement(visual, "headlight", ambient="0.55 0.55 0.55", diffuse="0.55 0.55 0.55")
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
        if child.tag in {"geom", "site"} or (child.tag == "body" and child.get("name") == "neck_pitch_assembly"):
            trunk.remove(child)
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


def pose(model, data, phase):
    """A small symmetric bend makes the four visible leg links easy to distinguish."""
    bend = 0.2 + 0.12 * math.sin(phase)
    targets = {
        "left_hip_pitch": -0.35,
        "left_knee": 0.7 + bend,
        "left_ankle": -0.35 - bend,
        "right_hip_pitch": 0.35,
        "right_knee": 0.7 + bend,
        "right_ankle": -0.35 - bend,
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
    args = parser.parse_args()
    model, data = load_legs()
    for _ in range(150):
        pose(model, data, 0)
    if args.preview:
        with mujoco.Renderer(model, height=480, width=640) as renderer:
            renderer.update_scene(data, camera=camera())
            pixels = renderer.render()
        from PIL import Image
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.asarray(pixels)).save(args.preview)
        print(f"Saved {args.preview}")
        return
    print("Showing only the two leg mechanisms. Close the viewer to quit.")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.lookat[:] = camera().lookat
        viewer.cam.distance = camera().distance
        viewer.cam.azimuth = camera().azimuth
        viewer.cam.elevation = camera().elevation
        start = time.monotonic()
        while viewer.is_running():
            pose(model, data, (time.monotonic() - start) * 2)
            viewer.sync()
            time.sleep(model.opt.timestep)


if __name__ == "__main__":
    main()
