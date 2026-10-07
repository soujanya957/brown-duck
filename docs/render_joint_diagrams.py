"""Render labelled joint diagrams of the duck for slides (16:9) into docs/images/.

Outputs:
  joints-split.png        legs (5 per leg) | head (4), labelled, 1920x1080
  joints-split-clean.png  same, markers only (add your own text in the slides)
  joints-legs.png         legs panel alone, 960x1080
  joints-head.png         head panel alone, 960x1080

Needs Pillow on top of the sim requirements:

    pip install pillow
    python docs/render_joint_diagrams.py
"""

from pathlib import Path

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "images"
SCENE = REPO / "sim" / "model" / "scene_flat_terrain.xml"
W, H = 960, 1080  # one panel; two side by side = 1920x1080

# Label order top to bottom (hip pitch sits outboard of hip roll, so listing it first avoids crossed lines).
LEFT_LEG = ["left_hip_yaw", "left_hip_pitch", "left_hip_roll", "left_knee", "left_ankle"]
RIGHT_LEG = [n.replace("left", "right") for n in LEFT_LEG]
HEAD = ["neck_pitch", "head_pitch", "head_yaw", "head_roll"]

BLUE, GREEN, ORANGE = (37, 99, 235), (22, 163, 74), (234, 88, 12)
INK, PAPER = (17, 24, 39), (255, 255, 255)


def font(size, bold=False):
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    for path in (f"/System/Library/Fonts/Supplemental/{name}", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def pretty(name):
    return name.replace("left_", "").replace("right_", "").replace("_", " ")


class Panel:
    def __init__(self, m, d, renderer, lookat, azimuth, elevation, distance):
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.azimuth, cam.elevation, cam.distance = azimuth, elevation, distance
        renderer.update_scene(d, cam)
        self.image = Image.fromarray(renderer.render()).convert("RGBA")
        gl = renderer.scene.camera[0]
        self.pos, self.fwd, self.up = np.array(gl.pos), np.array(gl.forward), np.array(gl.up)
        self.right = np.cross(self.fwd, self.up)
        self.hh = np.tan(np.deg2rad(m.vis.global_.fovy / 2))
        self.m, self.d = m, d

    def project(self, joint):
        v = self.d.xanchor[self.m.joint(joint).id] - self.pos
        z = v @ self.fwd
        u = (0.5 + (v @ self.right) / z / (2 * self.hh * W / H)) * W
        w = (0.5 - (v @ self.up) / z / (2 * self.hh)) * H
        return np.array([u, w])


def spread(ys, top, bottom, gap):
    """Push label y positions apart so they don't overlap, keeping order."""
    ys = list(ys)
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + gap)
    overflow = ys[-1] - bottom if ys else 0
    if overflow > 0:
        ys = [y - overflow for y in ys]
    return [max(y, top) for y in ys]


def annotate(panel, groups, title, subtitle, labels=True):
    """groups: list of (joint names, color, side 'left'|'right', group heading)."""
    img = panel.image
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(over)
    f_label, f_head = font(30), font(30, bold=True)
    for joints, color, side, heading in groups:
        pts = {j: panel.project(j) for j in joints}
        if labels:
            order = joints
            ys = spread(sorted(pts[j][1] for j in order), 250, H - 90, 62)
            x_text = 40 if side == "left" else W - 40
            anchor = "lm" if side == "left" else "rm"
            hx0, hy0, hx1, hy1 = g.textbbox((x_text, ys[0] - 66), heading, font=f_head, anchor=anchor)
            g.rounded_rectangle([hx0 - 12, hy0 - 8, hx1 + 12, hy1 + 8], radius=10, fill=color + (255,))
            g.text((x_text, ys[0] - 66), heading, font=f_head, fill=PAPER + (255,), anchor=anchor)
            for j, y in zip(order, ys):
                text = pretty(j)
                tw = g.textlength(text, font=f_label)
                x_end = x_text + tw + 14 if side == "left" else x_text - tw - 14
                g.line([(x_end, y), tuple(pts[j])], fill=color + (230,), width=3)
                g.rounded_rectangle(
                    [x_text - 10 if side == "left" else x_text - tw - 10, y - 22,
                     x_text + tw + 10 if side == "left" else x_text + 10, y + 22],
                    radius=10, fill=PAPER + (235,), outline=color + (255,), width=2,
                )
                g.text((x_text, y), text, font=f_label, fill=INK + (255,), anchor=anchor)
        for p in pts.values():
            g.ellipse([p[0] - 13, p[1] - 13, p[0] + 13, p[1] + 13], fill=color + (255,), outline=PAPER + (255,), width=4)
    if labels:
        g.rounded_rectangle([30, 30, W - 30, 170], radius=18, fill=PAPER + (230,))
        g.text((W / 2, 78), title, font=font(54, bold=True), fill=INK + (255,), anchor="mm")
        g.text((W / 2, 132), subtitle, font=font(30), fill=(75, 85, 99, 255), anchor="mm")
    return Image.alpha_composite(img, over).convert("RGB")


def main():
    m = mujoco.MjModel.from_xml_path(str(SCENE))
    m.vis.global_.offwidth, m.vis.global_.offheight = 1920, 1080  # runtime only
    d = mujoco.MjData(m)
    d.qpos[:] = m.keyframe("home").qpos
    mujoco.mj_forward(m, d)
    renderer = mujoco.Renderer(m, H, W)

    # Duck faces +x; azimuth 180 looks at its front, so its left leg is on the image's right.
    legs = Panel(m, d, renderer, lookat=(0, 0, 0.13), azimuth=160, elevation=-8, distance=0.62)
    head = Panel(m, d, renderer, lookat=(0.01, 0, 0.29), azimuth=130, elevation=-12, distance=0.55)
    leg_groups = [(RIGHT_LEG, GREEN, "left", "Right leg"), (LEFT_LEG, BLUE, "right", "Left leg")]
    head_groups = [(["head_yaw", "head_roll", "head_pitch", "neck_pitch"], ORANGE, "right", "Neck + head")]

    for labels, suffix in ((True, ""), (False, "-clean")):
        a = annotate(legs, leg_groups, "Legs: 5 joints each", "hip yaw · roll · pitch, knee, ankle", labels)
        b = annotate(head, head_groups, "Head: 4 joints", "neck pitch, head pitch · yaw · roll", labels)
        split = Image.new("RGB", (2 * W, H), PAPER)
        split.paste(a, (0, 0))
        split.paste(b, (W, 0))
        ImageDraw.Draw(split).line([(W, 0), (W, H)], fill=PAPER, width=6)
        split.save(OUT / f"joints-split{suffix}.png")
        if labels:
            a.save(OUT / "joints-legs.png")
            b.save(OUT / "joints-head.png")
    print("saved to", OUT)


if __name__ == "__main__":
    main()
