# Leg mechanism lab: Open Duck Mini v2

**Goal:** assemble one left leg, connect its servos on one Waveshare bus servo adapter, make a small supported step, and see how foot position maps to joint angles. The first leg is a mechanism test: it cannot walk across the floor by itself. A free-standing walk needs both legs, a body, balance and control.

Watch the [MuJoCo lower-body assembly animation](../docs/videos/leg-assembly.mp4) to see both leg and hip mechanisms. This lab builds the left leg first; use the step-by-step photos and notes below for details.

Run commands from the `brown-duck/` repository root. If this is your first lab, follow the [archived servo lab setup](servo-lab.md#1-get-ready) to install and activate the `brown-duck` environment. Bring the printed parts, five STS3215 servos for the full leg (or three for a hip-pitch/knee/ankle linkage), horns, bus cables, appropriate screws and bearings, a Waveshare bus servo adapter, USB cable and a regulated external servo supply.

## 1. Check parts and power

The full left leg has hip yaw **20**, hip roll **21**, hip pitch **22**, knee **23** and ankle **24**. The three pitch joints make the forward/back step; the yaw and roll joints can stay centered. Label each servo with its joint and ID before assembly. The [assembly overview](../hardware/ASSEMBLY.md#servo-ids) has the complete robot ID map.

| Printed part | Quantity for one left leg |
|---|---:|
| `roll_motor_top.stl`, `roll_motor_bottom.stl` | 1 each |
| `left_roll_to_pitch.stl`, `left_cache.stl` | 1 each |
| `knee_to_ankle_left_sheet.stl`, `knee_to_ankle_right_sheet.stl`, `leg_spacer.stl` | 2 each |
| `foot_top.stl`, `foot_side.stl`, `foot_bottom_pla.stl`, `foot_bottom_tpu.stl` | 1 each |

These are **14 printed pieces**. Files are in [`Open_Duck_Mini/print/`](../Open_Duck_Mini/print/); use the [full print list](../hardware/PRINT_LIST.md) for materials and settings. For the three-joint linkage, the foot and shin/thigh pieces are the priority; the yaw/roll mounts are for the full five-joint hip. Check the [upstream assembly photos](../Open_Duck_Mini/docs/assembly_guide.md#assemble-the-feet) and [CAD](https://cad.onshape.com/documents/64074dfcfa379b37d8a47762/w/3650ab4221e215a4f65eb7fe/e/0505c262d882183a25049d05) for horn, bearing and screw placement.

Read the **voltage on every actual servo label**. The stock duck BOM uses **7.4 V C001** servos; some earlier lab servos were **12 V C018/C047**. All servos on one chain must have the same rated voltage, and the Waveshare adapter's servo power input needs a supply at that voltage. USB supplies data, not motor power. Do not connect 7.4 V and 12 V motors to the same powered chain. See [servo variants](../hardware/SERVO_VARIANTS.md) if the labels differ.

## 2. Assign IDs, then daisy chain

With power **off**, connect only one servo to the adapter. Find the USB port using `python sim/duck_tools.py find-port`, then replace `PORT` below with the reported name. Power the servo from its correctly rated supply. For each joint, scan, assign its ID if needed, power cycle and verify. Example for a knee that arrived as ID 1:

```bash
python sim/servo_lab.py scan --port PORT --last 253
python sim/servo_lab.py set-id --port PORT --old-id 1 --new-id 23
# Turn servo power off and on, then:
python sim/servo_lab.py status --port PORT --ids 23
```

If it already has ID 23, skip `set-id`. Repeat for the other motors **one at a time**. The prompted shortcut is `python sim/duck_tools.py setup-motors --port PORT --robot left-leg`; it configures all five IDs and centers each unloaded servo. Keep horns off while centering; install them only after each motor has reached its intended zero. Note the hip-pitch servo orientation shown in the [thigh assembly photo](../Open_Duck_Mini/docs/assembly_guide.md#assemble-the-thighs).

After every servo has a unique ID, turn power off and connect **adapter → first servo → next servo → ...** using the second socket on each servo. The chain order does not set the ID. Power on and check all connected IDs (use `22 23 24` for a three-joint linkage):

```bash
python sim/servo_lab.py status --port PORT --ids 20 21 22 23 24
```

The reported voltage should match the labels. If an ID is missing, power off and scan that servo alone. The [daisy-chain guide](../hardware/SERVO_DAISY_CHAIN.md) has detailed troubleshooting.

## 3. Assemble and check motion

Follow the [assembly guide](../Open_Duck_Mini/docs/assembly_guide.md) in this order: **foot → shin → thigh → hip**. Route the ankle cable through the shin sheet before closing it. Match the mirrored left hip part and the hip-pitch zero orientation. Use blue Loctite 243 only for metal-to-metal screws into the servos, never on plastic. Turn power off when changing cables or horns.

Support or clamp the hip securely and keep the foot clear of the table. Check each joint's mechanical clearance by hand **with torque off** before powering. Start with a small movement on the unloaded or supported knee; `sweep` measures the current position and returns to it:

```bash
python sim/servo_lab.py sweep --port PORT --id 23 --amplitude 5 --speed 40
python sim/servo_lab.py status --port PORT --ids 22 23 24
```

A sweep that is safe for an unloaded servo may still hit a printed part. Watch the whole linkage, stop immediately if it binds, and reduce the range. Keep hands out of the linkage while powered. Record which direction each joint moves and the observed safe limits. The calibration command can record centers and limits after assembly: `python sim/duck_tools.py calibrate --port PORT --robot left-leg` (torque off; move the joints by hand). Save and inspect `calibration/left-leg.json` before planning larger motions.

## 4. Make a small step and explore IK

Start in the simulator. From the activated environment run:

```bash
mjpython sim/legs.py --gait   # macOS
python sim/legs.py --gait     # Linux / Windows
```

The hips are fixed in the viewer. The feet alternate a short **stance sweep** and a raised **swing return**. This shows a stepping mechanism, not a balanced walking controller. Close the viewer to stop. Without `--gait`, `sim/legs.py` shows the older slow knee bend.

The code's [`two_link_ik`](../sim/legs.py) treats the hip-to-knee and knee-to-ankle distances as **0.07865 m** each, taken from the MuJoCo model. Given ankle target `(x, z)` relative to the hip, it computes knee bend with the law of cosines, then subtracts the shin angle from the direction to the foot to get hip pitch. Ankle pitch offsets the hip and knee to keep the foot approximately level. The two legs use mirrored hip signs in the model. **These model angles are not servo ticks:** real horns can have different centers and directions, so do not send the simulator's angles to assembled hardware without checking each joint's calibration and limits.

For a simple **two-leg IK walk**, run `mjpython sim/ik_walk.py` on macOS or
`python sim/ik_walk.py` on Linux/Windows. The [walking clip](../docs/videos/ik-walk.mp4)
shows the result. `python sim/ik_walk.py --check` verifies that the stance feet stay
within 1 mm of their world positions and the swing feet lift. The script holds the
pelvis upright and advances it at the speed of the backward stance sweep; it does not
model balance or command the physical servos.

The [standalone lower-body URDF](../sim/model/lower_body.urdf) can be viewed with the
same gait: `mjpython sim/urdf_walk.py` on macOS or `python sim/urdf_walk.py` on
Linux/Windows. Run `python sim/urdf_walk.py --check` for a no-window check, or watch
the [URDF walking clip](../docs/videos/urdf-walk.mp4). The [README](../README.md#2-watch-the-build-and-open-the-walking-simulator)
has the setup and daisy-chain commands.

For the physical one-leg milestone, use the supported linkage and small individual `sweep` commands to create a lift, forward motion and return. Write down the three joint positions that produce each phase. Once both legs and a supported body are assembled and calibrated, those phases can be alternated for a walking experiment. The [full walking simulator](../sim/README.md) demonstrates a trained controller for the complete duck.

**Discuss:** Why do IDs have to differ? Why does a knee bend change foot height even when hip pitch stays still? What happens when a requested foot position is farther than the two links can reach? Which measurements are needed before model angles can be used on real hardware?

## After both legs are assembled: calibration and exploration

Connect and verify all ten unique IDs, then follow the [README's lower-body sequence](../README.md#after-both-legs-and-hips-are-assembled):

1. `python sim/duck_tools.py calibrate --port PORT --robot lower-body` turns torque off, displays current/min/max positions live, and saves `calibration/lower-body.json`.
2. `python sim/duck_tools.py joint-teleop --port PORT` lets you type one small command such as `left_knee +5`; `read` displays every position and calibrated range.
3. Use `mjpython sim/urdf_walk.py --target 0.01 -0.145` on macOS or `python sim/urdf_walk.py --target 0.01 -0.145` on Linux/Windows to inspect one IK target. Then open `sim/urdf_walk.py` without `--target` to watch the gait.

Support the lower body throughout calibration and motor control. Record what a positive tick change actually does before comparing physical joints with model angles:

| Joint | ID | Neutral ticks | Safe min–max | Motion from `+5` |
|---|---:|---:|---|---|
| Right hip yaw | 10 | | | |
| Right hip roll | 11 | | | |
| Right hip pitch | 12 | | | |
| Right knee | 13 | | | |
| Right ankle | 14 | | | |
| Left hip yaw | 20 | | | |
| Left hip roll | 21 | | | |
| Left hip pitch | 22 | | | |
| Left knee | 23 | | | |
| Left ankle | 24 | | | |
