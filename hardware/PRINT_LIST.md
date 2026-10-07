# Print list

Checklist of every part to 3D print for one Open Duck Mini v2, from
[`Open_Duck_Mini/docs/print_guide.md`](../Open_Duck_Mini/docs/print_guide.md). The STLs live in
[`Open_Duck_Mini/print/`](../Open_Duck_Mini/print/) (our fork, as a submodule); we link to them instead of copying them here.
Links below work in a local clone (`git clone --recursive`). On github.com, browse them at
[soujanya957/Open_Duck_Mini/print](https://github.com/soujanya957/Open_Duck_Mini/tree/main/print).

## Settings

- **PLA, 15 % infill** for everything, except
- **`foot_bottom_tpu.stl`: TPU, 40 % infill** (the foot soles).
- Bambu printers: the ready-made [MakerWorld profile](https://makerworld.com/en/models/2755651) has all parts on 6 plates (~53 h).

**36 files, 51 parts.** Print the feet and legs first: we build and test one leg before anything else.
Tick the box (`[ ]` → `[x]`) and put your name in *printed by* when a part is done. Fill in *subassembly*
(where the part goes on the robot, e.g. "left foot, top") as you find it in the CAD; see [`activities/hardware.md`](../activities/hardware.md).
Community mods (BD-X style head, covers, stand) are in [`print/mods/`](../Open_Duck_Mini/print/mods/) and are not on this list.

## Feet (8 parts)

| done | file | qty | material | subassembly | printed by |
|:---:|---|---:|---|---|---|
| [ ] | [`foot_top.stl`](../Open_Duck_Mini/print/foot_top.stl) | 2 | PLA 15 % |  |  |
| [ ] | [`foot_side.stl`](../Open_Duck_Mini/print/foot_side.stl) | 2 | PLA 15 % |  |  |
| [ ] | [`foot_bottom_pla.stl`](../Open_Duck_Mini/print/foot_bottom_pla.stl) | 2 | PLA 15 % |  |  |
| [ ] | [`foot_bottom_tpu.stl`](../Open_Duck_Mini/print/foot_bottom_tpu.stl) | 2 | TPU 40 % |  |  |

## Legs (shins + thighs) (14 parts)

| done | file | qty | material | subassembly | printed by |
|:---:|---|---:|---|---|---|
| [ ] | [`knee_to_ankle_left_sheet.stl`](../Open_Duck_Mini/print/knee_to_ankle_left_sheet.stl) | 4 | PLA 15 % |  |  |
| [ ] | [`knee_to_ankle_right_sheet.stl`](../Open_Duck_Mini/print/knee_to_ankle_right_sheet.stl) | 4 | PLA 15 % |  |  |
| [ ] | [`leg_spacer.stl`](../Open_Duck_Mini/print/leg_spacer.stl) | 4 | PLA 15 % |  |  |
| [ ] | [`left_cache.stl`](../Open_Duck_Mini/print/left_cache.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`right_cache.stl`](../Open_Duck_Mini/print/right_cache.stl) | 1 | PLA 15 % |  |  |

## Hips (6 parts)

| done | file | qty | material | subassembly | printed by |
|:---:|---|---:|---|---|---|
| [ ] | [`left_roll_to_pitch.stl`](../Open_Duck_Mini/print/left_roll_to_pitch.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`right_roll_to_pitch.stl`](../Open_Duck_Mini/print/right_roll_to_pitch.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`roll_motor_bottom.stl`](../Open_Duck_Mini/print/roll_motor_bottom.stl) | 2 | PLA 15 % |  |  |
| [ ] | [`roll_motor_top.stl`](../Open_Duck_Mini/print/roll_motor_top.stl) | 2 | PLA 15 % |  |  |

## Trunk (2 parts)

| done | file | qty | material | subassembly | printed by |
|:---:|---|---:|---|---|---|
| [ ] | [`trunk_bottom.stl`](../Open_Duck_Mini/print/trunk_bottom.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`trunk_top.stl`](../Open_Duck_Mini/print/trunk_top.stl) | 1 | PLA 15 % |  |  |

## Neck + head (7 parts)

| done | file | qty | material | subassembly | printed by |
|:---:|---|---:|---|---|---|
| [ ] | [`neck_left_sheet.stl`](../Open_Duck_Mini/print/neck_left_sheet.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`neck_right_sheet.stl`](../Open_Duck_Mini/print/neck_right_sheet.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`head_pitch_to_yaw.stl`](../Open_Duck_Mini/print/head_pitch_to_yaw.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`head_yaw_to_roll.stl`](../Open_Duck_Mini/print/head_yaw_to_roll.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`head_roll_mount.stl`](../Open_Duck_Mini/print/head_roll_mount.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`head.stl`](../Open_Duck_Mini/print/head.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`head_bot_sheet.stl`](../Open_Duck_Mini/print/head_bot_sheet.stl) | 1 | PLA 15 % |  |  |

## Body shell (5 parts)

| done | file | qty | material | subassembly | printed by |
|:---:|---|---:|---|---|---|
| [ ] | [`body_front.stl`](../Open_Duck_Mini/print/body_front.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`body_middle_bottom.stl`](../Open_Duck_Mini/print/body_middle_bottom.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`body_middle_top.stl`](../Open_Duck_Mini/print/body_middle_top.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`body_back.stl`](../Open_Duck_Mini/print/body_back.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`battery_pack_lid.stl`](../Open_Duck_Mini/print/battery_pack_lid.stl) | 1 | PLA 15 % |  |  |

## Expression extras (optional: eyes, antennas, flashlight/projector, speaker) (9 parts)

| done | file | qty | material | subassembly | printed by |
|:---:|---|---:|---|---|---|
| [ ] | [`left_eye.stl`](../Open_Duck_Mini/print/left_eye.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`right_eye.stl`](../Open_Duck_Mini/print/right_eye.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`left_antenna_holder.stl`](../Open_Duck_Mini/print/left_antenna_holder.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`right_antenna_holder.stl`](../Open_Duck_Mini/print/right_antenna_holder.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`bulb.stl`](../Open_Duck_Mini/print/bulb.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`flash_light_module.stl`](../Open_Duck_Mini/print/flash_light_module.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`flash_reflector_interface.stl`](../Open_Duck_Mini/print/flash_reflector_interface.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`speaker_interface.stl`](../Open_Duck_Mini/print/speaker_interface.stl) | 1 | PLA 15 % |  |  |
| [ ] | [`speaker_stand.stl`](../Open_Duck_Mini/print/speaker_stand.stl) | 1 | PLA 15 % |  |  |
