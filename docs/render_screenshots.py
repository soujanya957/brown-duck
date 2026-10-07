"""Regenerate the README pictures in docs/images/ (offscreen, no window).

Runs sim/teleop.py's model, policy and key handling with scripted key presses and renders
stills + a walking GIF with mujoco.Renderer. Needs Pillow on top of the sim requirements:

    pip install pillow
    python docs/render_screenshots.py
"""
import contextlib
import sys
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO / "sim"))
import teleop  # noqa: E402

duck = teleop.MjInfer(
    teleop.HERE / "model" / "scene_flat_terrain.xml",
    teleop.HERE / "data" / "polynomial_coefficients.pkl",
    teleop.HERE / "policies" / "BEST_WALK_ONNX_2.onnx",
    standing=False,
)
m, d = duck.model, duck.data
m.vis.global_.offwidth, m.vis.global_.offheight = 1280, 720  # runtime only, XML untouched
renderer = mujoco.Renderer(m, 720, 1280)
gif_renderer = mujoco.Renderer(m, 360, 640)
trunk = m.body("trunk_assembly").id

cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE


def shot(r, azimuth, elevation, distance):
    cam.lookat[:] = d.xpos[trunk] + np.array([0, 0, 0.07])
    cam.azimuth, cam.elevation, cam.distance = azimuth, elevation, distance
    r.update_scene(d, cam)
    return Image.fromarray(r.render())


K = teleop
keys = [(1.0, K.KEY_W), (7.0, K.KEY_A), (9.5, K.KEY_H), (9.6, K.KEY_W), (12.0, K.KEY_LEFT), (14.0, K.KEY_Q)]
# (time, filename, azimuth, elevation, distance)
stills = [
    (0.8, "sim-standing.png", 210, -15, 1.0),
    (4.33, "sim-walking-side.png", 90, -10, 1.0),
    (8.6, "sim-turning.png", 150, -35, 1.1),
    (13.5, "sim-head-yaw.png", 200, -12, 0.8),
]
gif_window = (2.0, 6.0)
gif_frames, hooks = [], {}


class DummyViewer:
    def is_running(self):
        return d.time < 15.0

    def sync(self):
        if keys and d.time >= keys[0][0]:
            hooks["cb"](keys.pop(0)[1])
        if stills and d.time >= stills[0][0]:
            _, name, az, el, dist = stills.pop(0)
            shot(renderer, az, el, dist).save(OUT / name)
            print("saved", name, "z=%.3f" % d.qpos[2])
        step = round(d.time / m.opt.timestep)
        if gif_window[0] <= d.time < gif_window[1] and step % 33 == 0:  # ~15 fps
            gif_frames.append(shot(gif_renderer, 135, -15, 1.0))

    def lock(self):
        return contextlib.nullcontext()


@contextlib.contextmanager
def fake_launch_passive(model, data, key_callback=None, **kw):
    hooks["cb"] = key_callback
    yield DummyViewer()


mujoco.viewer.launch_passive = fake_launch_passive
teleop.time.sleep = lambda s: None
duck.run()

frames = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in gif_frames]
frames[0].save(OUT / "sim-walking.gif", save_all=True, append_images=frames[1:], duration=66, loop=0, optimize=True)
print("saved sim-walking.gif", len(frames), "frames")
