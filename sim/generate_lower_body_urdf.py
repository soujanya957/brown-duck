"""Extract the two legs and inner pelvis from the upstream Open Duck Mini v2 URDF."""

import copy
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/robot.urdf"
OUTPUT = ROOT / "sim/model/lower_body.urdf"
MESH_DIR = "../../Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2"
PELVIS_MESHES = {
    "trunk_top.stl", "trunk_bottom.stl", "roll_bearing.stl",
    "wj-wk00-0123middlecase_56.stl", "wj-wk00-0124bottomcase_45.stl",
    "wj-wk00-0122topcabinetcase_95.stl", "drive_palonier.stl",
    "passive_palonier.stl",
}
EXTERIOR_COVERS = {"left_cache.stl", "right_cache.stl"}
LEG_JOINTS = {f"{side}_{joint}" for side in ("left", "right")
              for joint in ("hip_yaw", "hip_roll", "hip_pitch", "knee", "ankle", "foot_frame")}


def generate():
    source = ET.parse(SOURCE).getroot()
    root = ET.Element("robot", name="open_duck_mini_v2_lower_body")
    mujoco = ET.SubElement(root, "mujoco")
    ET.SubElement(mujoco, "compiler", fusestatic="false", strippath="false",
                  discardvisual="false")

    joints = [joint for joint in source.findall("joint")
              if joint.get("name") in LEG_JOINTS]
    names = {"trunk_assembly"}
    for joint in joints:
        names.add(joint.find("parent").get("link"))
        names.add(joint.find("child").get("link"))

    for source_link in source.findall("link"):
        if source_link.get("name") not in names:
            continue
        link = copy.deepcopy(source_link)
        for collision in list(link.findall("collision")):
            link.remove(collision)
        for visual in list(link.findall("visual")):
            mesh = visual.find("./geometry/mesh")
            if mesh is None:
                continue
            name = Path(mesh.get("filename")).name
            if name in EXTERIOR_COVERS or (link.get("name") == "trunk_assembly"
                                            and name not in PELVIS_MESHES):
                link.remove(visual)
            else:
                mesh.set("filename", f"{MESH_DIR}/{name}")
        if link.find("inertial") is None:
            inertial = ET.SubElement(link, "inertial")
            ET.SubElement(inertial, "origin", xyz="0 0 0", rpy="0 0 0")
            ET.SubElement(inertial, "mass", value="0.5" if link.get("name") == "trunk_assembly" else "0.1")
            ET.SubElement(inertial, "inertia", ixx="0.0001", ixy="0", ixz="0",
                          iyy="0.0001", iyz="0", izz="0.0001")
        root.append(link)

    for joint in joints:
        root.append(copy.deepcopy(joint))
    ET.indent(root, space="  ")
    OUTPUT.write_text('<?xml version="1.0"?>\n'
                      '<!-- Generated from the upstream Open Duck Mini v2 URDF by sim/generate_lower_body_urdf.py. -->\n'
                      '<!-- Inertias are placeholders and collisions are omitted: use this for kinematic viewing, not dynamics. -->\n'
                      + ET.tostring(root, encoding="unicode") + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(names)} links, {len(joints)} joints")


if __name__ == "__main__":
    generate()
