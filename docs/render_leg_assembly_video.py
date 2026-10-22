"""Render a MuJoCo exploded assembly of the Open Duck Mini lower body.

Source geometry and final poses come from the Open_Duck_Mini v2 robot.xml model.
Requires the brown-duck conda environment, FFmpeg and ImageMagick.

    python docs/render_leg_assembly_video.py --preview /tmp/leg-preview.png
    python docs/render_leg_assembly_video.py
"""

from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/robot.xml"
VIDEO = ROOT / "docs/videos/leg-assembly.mp4"
POSTER = ROOT / "docs/images/leg-assembly-poster.png"
FONT = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
if not FONT.exists():
    FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

STEPS = [
    "01  PLA bases and TPU soles",
    "02  Foot tops and sides",
    "03  Seat both ankle servos",
    "04  Fit the shin sheets and spacers",
    "05  Seat both knee servos",
    "06  Fit the thigh sheets and spacers",
    "07  Hip pitch servos and mirrored brackets",
    "08  Hip roll servos",
    "09  Fit both yaw mounts",
    "10  Join both hips at the inner pelvis",
    "11  Check alternating supported bends",
]
STEP_SECONDS = 2.8
DURATION = len(STEPS) * STEP_SECONDS
SERVO_MESHES = {
    "wj-wk00-0123middlecase_56", "wj-wk00-0124bottomcase_45",
    "wj-wk00-0122topcabinetcase_95", "drive_palonier", "passive_palonier",
}
OFFSETS = [
    (-0.09, 0.00, 0.00), (0.09, 0.00, 0.00), (0.00, -0.10, 0.00),
    (0.09, 0.00, 0.00), (0.00, -0.10, 0.00), (0.09, 0.00, 0.00),
    (0.00, -0.11, 0.00), (0.00, -0.10, 0.00), (0.09, 0.00, 0.00),
    (0.00, -0.10, 0.00), (0.00, 0.00, 0.00),
]


def smoothstep(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def stage(body: str, mesh: str, local_y: float) -> int | None:
    if mesh in {"left_cache", "right_cache"}:  # exterior covers, not the mechanism
        return None
    if body in {"foot_assembly", "foot_assembly_2"}:
        return 0 if mesh in {"foot_bottom_tpu", "foot_bottom_pla"} else 1
    if body in {"knee_and_ankle_assembly_2", "knee_and_ankle_assembly_4"}:
        return 2 if mesh in SERVO_MESHES else 3
    if body in {"knee_and_ankle_assembly", "knee_and_ankle_assembly_3"}:
        return 4 if mesh in SERVO_MESHES else 5
    if body in {"left_roll_to_pitch_assembly", "right_roll_to_pitch_assembly"}:
        return 6
    if body in {"hip_roll_assembly", "hip_roll_assembly_2"}:
        return 7 if mesh in SERVO_MESHES else 8
    if body == "trunk_assembly" and mesh in {"trunk_bottom", "trunk_top", "roll_bearing"}:
        return 9
    if body == "trunk_assembly" and abs(local_y) > 0.02 and mesh in SERVO_MESHES:
        return 9
    return None


def model_and_parts():
    source = mujoco.MjModel.from_xml_path(str(SOURCE))
    source_data = mujoco.MjData(source)
    mujoco.mj_forward(source, source_data)
    assets = {e.attrib["name"]: SOURCE.parent / e.attrib["file"]
              for e in ET.parse(SOURCE).findall("./asset/mesh")}
    parts = []
    for i in range(source.ngeom):
        if source.geom_type[i] != mujoco.mjtGeom.mjGEOM_MESH:
            continue
        mesh = source.mesh(int(source.geom_dataid[i])).name
        body = source.body(int(source.geom_bodyid[i])).name
        group = stage(body, mesh, float(source.geom_pos[i, 1]))
        if group is not None:
            parts.append((i, mesh, group))
    assert len(parts) >= 70, f"Expected both lower-body mechanisms, found {len(parts)}"
    referenced = {mesh for _, mesh, _ in parts}
    asset_xml = "".join(
        f'<mesh name="{escape(mesh)}" file="{escape(str(assets[mesh]))}"/>'
        for mesh in sorted(referenced)
    )
    bodies = "".join(
        f'<body name="part_{i}" mocap="true"><geom type="mesh" mesh="{escape(mesh)}" '
        f'rgba="{" ".join(str(float(x)) for x in source.geom_rgba[i])}" '
        'contype="0" conaffinity="0"/></body>'
        for i, mesh, _ in parts
    )
    xml = f'''<mujoco model="lower body exploded assembly">
      <visual><headlight ambient="0.48 0.48 0.48" diffuse="0.58 0.58 0.58"/>
        <global offwidth="1920" offheight="1080"/></visual>
      <asset>
        <texture type="skybox" builtin="gradient" rgb1="0.35 0.48 0.64"
          rgb2="0.06 0.09 0.15" width="512" height="512"/>
        <texture name="grid" type="2d" builtin="checker" rgb1="0.22 0.25 0.29"
          rgb2="0.17 0.19 0.22" width="512" height="512"/>
        <material name="floor" texture="grid" texrepeat="14 14"/>
        {asset_xml}
      </asset>
      <worldbody>
        <light pos="0.3 -0.4 1.1" dir="-0.3 0.4 -1" diffuse="0.8 0.8 0.8"/>
        <geom type="plane" pos="0 0 0.18" size="2 2 0.01" material="floor"/>
        {bodies}
      </worldbody>
    </mujoco>'''
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    return source, source_data, model, data, parts


def set_poses(source, source_data, model, data, parts, t):
    source_data.qpos[:] = source.qpos0
    if t >= 10 * STEP_SECONDS:
        phase = (t - 10 * STEP_SECONDS) / STEP_SECONDS
        left = math.sin(math.pi * phase) ** 2
        right = math.sin(math.pi * (phase + 0.5)) ** 2
        for name, angle in (("left_hip_pitch", -0.13 * left),
                            ("left_knee", 0.26 * left), ("left_ankle", -0.13 * left),
                            ("right_hip_pitch", 0.13 * right),
                            ("right_knee", 0.26 * right), ("right_ankle", -0.13 * right)):
            source_data.qpos[source.joint(name).qposadr[0]] = angle
    mujoco.mj_forward(source, source_data)
    for i, _, group in parts:
        mocap = int(model.body(f"part_{i}").mocapid[0])
        geom_id = int(model.body_geomadr[model.body(f"part_{i}").id])
        local_rotation = np.zeros((3, 3))
        mujoco.mju_quat2Mat(local_rotation.ravel(), model.geom_quat[geom_id])
        world_rotation = source_data.geom_xmat[i].reshape(3, 3)
        body_rotation = world_rotation @ local_rotation.T
        quat = np.zeros(4)
        mujoco.mju_mat2Quat(quat, body_rotation.ravel())
        start = group * STEP_SECONDS
        assembled = smoothstep((t - start) / 1.65)
        offset = np.asarray(OFFSETS[group]) * (1 - assembled)
        side = 1 if source_data.geom_xpos[i, 1] >= 0 else -1
        offset[1] *= side
        data.mocap_quat[mocap] = quat
        data.mocap_pos[mocap] = source_data.geom_xpos[i] - body_rotation @ model.geom_pos[geom_id] + offset
    mujoco.mj_forward(model, data)


def render_frame(renderer, source, source_data, model, data, parts, t):
    set_poses(source, source_data, model, data, parts, t)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = [-0.025, 0.0, 0.33]
    cam.distance = 0.68
    cam.azimuth = 125 + 15 * t / DURATION
    cam.elevation = -17
    renderer.update_scene(data, camera=cam)
    return renderer.render()


def caption_overlays(folder: Path, width: int, height: int) -> list[Path]:
    paths = []
    for index, label in enumerate(STEPS):
        path = folder / f"step-{index}.png"
        subprocess.run([
            "magick", "-size", f"{width}x{height}", "xc:none",
            "-fill", "#08121ccc", "-draw", f"rectangle 0,0 {width},68",
            "-fill", "#08121cdd", "-draw", f"rectangle 0,{height-88} {width},{height}",
            "-font", str(FONT), "-fill", "white", "-pointsize", str(max(20, width // 45)),
            "-annotate", "+26+18", "OPEN DUCK MINI  /  LOWER BODY ASSEMBLY",
            "-pointsize", str(max(20, width // 39)), "-annotate", f"+26+{height-63}",
            label, str(path),
        ], check=True)
        paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--size", default="1280x720")
    parser.add_argument("--preview", type=Path, help="write a six-frame contact sheet")
    args = parser.parse_args()
    width, height = map(int, args.size.split("x"))
    source, source_data, model, data, parts = model_and_parts()
    with mujoco.Renderer(model, height, width) as renderer:
        if args.preview:
            with tempfile.TemporaryDirectory() as temp:
                frames = []
                for n, t in enumerate((1, 6, 11, 17, 23, 30)):
                    rgb = render_frame(renderer, source, source_data, model, data, parts, t)
                    path = Path(temp) / f"frame-{n}.png"
                    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                                    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", args.size,
                                    "-i", "-", "-frames:v", "1", str(path)], input=rgb.tobytes(), check=True)
                    frames.append(str(path))
                subprocess.run(["magick", "montage", *frames, "-tile", "3x2", "-geometry",
                                f"{width}x{height}+0+0", str(args.preview)], check=True)
            print(f"Wrote {args.preview}")
            return
        VIDEO.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "raw.mp4"
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                   "-pix_fmt", "rgb24", "-s", args.size, "-r", str(args.fps), "-i", "-",
                   "-c:v", "libx264", "-crf", "21", "-preset", "medium",
                   "-pix_fmt", "yuv420p", str(raw)]
            encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            try:
                for frame in range(math.ceil(DURATION * args.fps)):
                    rgb = render_frame(renderer, source, source_data, model, data, parts,
                                       frame / args.fps)
                    encoder.stdin.write(rgb.tobytes())
            finally:
                encoder.stdin.close()
            if encoder.wait() != 0:
                raise RuntimeError("FFmpeg failed to encode the assembly video")
            overlays = caption_overlays(Path(temp), width, height)
            filters = []
            for index in range(len(STEPS)):
                inp = "[0:v]" if index == 0 else f"[v{index}]"
                start, end = index * STEP_SECONDS, (index + 1) * STEP_SECONDS
                filters.append(f"{inp}[{index+1}:v]overlay=enable='between(t,{start:.2f},{end:.2f})'[v{index+1}]")
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
                *[item for path in overlays for item in ("-loop", "1", "-i", str(path))],
                "-filter_complex", ";".join(filters), "-map", f"[v{len(STEPS)}]",
                "-t", str(DURATION), "-c:v", "libx264", "-crf", "21", "-preset", "medium",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(VIDEO),
            ], check=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss",
                        str(DURATION - 0.5), "-i", str(VIDEO), "-frames:v", "1", str(POSTER)],
                       check=True)
    print(f"Wrote {VIDEO} and {POSTER}")


if __name__ == "__main__":
    main()
